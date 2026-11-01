import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed

@pytest.mark.parametrize('category',['kitchen','bathroom','restaurant','garden','exterior','landscape','dining'])
def test_new_category_needs_real_rate_and_can_plan_when_configured(monkeypatch,category):
    seed()
    monkeypatch.delenv('LABOR_RATES_JSON',raising=False)
    body={'budget':5000,'budget_confirmed':True,'currency':'USD','preference':'either','style':'modern','room_category':category,'room_area':24}
    with TestClient(app) as client:
        missing=client.post('/api/plans',json=body)
        assert missing.status_code==422,missing.text
        assert 'labor rate' in missing.json()['detail']
        monkeypatch.setenv('LABOR_RATES_JSON','{"USD":{"'+category+'":4}}')
        proposal=client.post('/api/plans',json=body)
        assert proposal.status_code==201,proposal.text
        assert proposal.json()['quote']['labor']==96
        assert proposal.json()['asset_ids']
