import base64
import json
from io import BytesIO
import httpx
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed

def image():
    buf=BytesIO();Image.new('RGB',(128,128),'beige').save(buf,'PNG');return buf.getvalue()

@pytest.mark.parametrize('provider',['openai','gemini'])
def test_real_endpoint_with_simulated_provider(monkeypatch,provider):
    seed()
    monkeypatch.setenv('ROOM_OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setenv('ROOM_GEMINI_API_KEY','not-a-real-key')
    real_client=httpx.AsyncClient
    seen=[]
    def handler(request):
        seen.append(request)
        encoded=base64.b64encode(image()).decode()
        if provider=='openai':
            assert request.url.path=='/v1/images/edits'
            assert request.content.count(b'name="image[]"')==3
            assert b'width' in request.content and b'Preserve product identity' in request.content
            assert b'Keep a calm reading corner' in request.content
            return httpx.Response(200,json={'data':[{'b64_json':encoded}]})
        payload=json.loads(request.content)
        parts=payload['contents'][0]['parts']
        assert len(parts)==4
        assert 'Keep a calm reading corner' in parts[0]['text']
        assert all('inlineData' in p for p in parts[1:])
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'inlineData':{'data':encoded}}]}}]})
    monkeypatch.setattr('app.generation.httpx.AsyncClient',lambda **kw:real_client(transport=httpx.MockTransport(handler),**kw))
    with TestClient(app) as c:
        data={'style':'modern','asset_ids':'["sofa","lamp"]','room_area':'25','room_category':'living','model':provider,'design_brief':'Keep a calm reading corner'}
        assert c.post('/api/designs',data=data,files={'room':('room.png',image())}).status_code==422
        data['ai_consent']='true'
        r=c.post('/api/designs',data=data,files={'room':('room.png',image())})
        assert r.status_code==201,r.text
        result=r.json()
        assert result['render_mode']=='ai_reference' and result['quote']['product_fidelity']=='unverified'
        assert result['quote']['items_subtotal']==1035
        assert len(result['placements'])==2 and len(seen)==1

def test_unconfigured_model_and_no_key_exposure(monkeypatch):
    monkeypatch.delenv('ROOM_OPENAI_API_KEY',raising=False)
    with TestClient(app) as c:
        models=c.get('/api/models').json()
        assert not next(m for m in models if m['id']=='openai')['available']
        r=c.post('/api/designs',data={'model':'openai','ai_consent':'true','style':'modern','asset_ids':'["sofa"]','room_area':'25','room_category':'living'},files={'room':('room.png',image())})
        assert r.status_code==503
