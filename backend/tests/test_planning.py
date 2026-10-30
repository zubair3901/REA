from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed
from app.database import Session
from app.models import Asset
from test_generation import image

def params(**overrides):
    return {'budget':1500,'budget_confirmed':True,'currency':'USD','preference':'new','style':'minimalist','room_category':'living','room_area':25,**overrides}

def test_budget_matching_and_confirmation():
    seed()
    with TestClient(app) as c:
        assert c.post('/api/plans',json=params(budget_confirmed=False)).status_code==422
        assert c.post('/api/plans',json=params(budget=10)).status_code==409
        assert c.post('/api/plans',json=params(preference='used',currency='EUR')).status_code==409
        r=c.post('/api/plans',json=params())
        assert r.status_code==201,r.text
        p=r.json()
        assert p['quote']['total']<=1500 and p['remaining_budget']>=0
        assert len(p['asset_ids'])==len(set(p['asset_ids']))
        assert c.post('/api/plans',json=params(latitude=0,longitude=0)).status_code==409

def test_plan_rechecks_price_before_render():
    seed()
    with TestClient(app) as c:
        p=c.post('/api/plans',json=params()).json()
        with Session() as db:
            item=db.get(Asset,p['asset_ids'][0]);old=item.price;item.price=2000;db.commit()
        try:
            data={'style':'minimalist','asset_ids':'[]','room_area':25,'room_category':'living','plan_id':p['id']}
            r=c.post('/api/designs',data=data,files={'room':('room.png',image())})
            assert r.status_code==409,r.text
        finally:
            with Session() as db:db.get(Asset,p['asset_ids'][0]).price=old;db.commit()

def test_confirmed_plan_renders_without_manual_asset_selection():
    seed()
    with TestClient(app) as c:
        p=c.post('/api/plans',json=params()).json()
        r=c.post('/api/designs',data={'style':'minimalist','asset_ids':'[]','room_area':25,'room_category':'living','plan_id':p['id']},files={'room':('room.png',image())})
        assert r.status_code==201,r.text
        assert r.json()['quote']['total']<=1500
        assert {x['asset_id'] for x in r.json()['placements']}==set(p['asset_ids'])

def test_preowned_selection_excludes_new_inventory():
    seed()
    with Session() as db:
        chair=db.get(Asset,'chair');old=chair.condition;chair.condition='good';db.commit()
    try:
        with TestClient(app) as c:
            p=c.post('/api/plans',json=params(preference='used')).json()
            with Session() as db:
                assert all(db.get(Asset,i).condition!='new' for i in p['asset_ids'])
    finally:
        with Session() as db:db.get(Asset,'chair').condition=old;db.commit()
