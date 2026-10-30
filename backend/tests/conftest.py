"""Initialize a disposable database before ANY application import."""
import os
import tempfile
os.environ['DATA_DIR']=tempfile.mkdtemp(prefix='roomform-test-')
os.environ.pop('DATABASE_URL',None)
if os.getenv('ROOM_TEST_POSTGRES_URL'):
    assert os.environ['ROOM_TEST_POSTGRES_URL'].endswith('/roomform_test')
    os.environ['DATABASE_URL']=os.environ['ROOM_TEST_POSTGRES_URL']
os.environ['ALLOW_GUEST_PREVIEWS']='true'
os.environ['ENABLE_AI_GENERATION']='true'
os.environ['MERCHANT_KEYS_JSON']='{"demo":"test-key"}'

import pytest
@pytest.fixture(autouse=True)
def isolated_database():
    from app.database import Base,engine
    import app.models
    assert (engine.url.get_backend_name()=='sqlite' and 'roomform-test-' in str(engine.url.database)) or (os.getenv('ROOM_TEST_POSTGRES_URL') and engine.url.database=='roomform_test'), 'Refuse to reset a non-test database'
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

os.environ['ALLOW_LEGACY_OPERATOR_KEY']='true'

os.environ['ALLOW_DEMO_CATALOG']='true'
os.environ['ALLOW_LEGACY_PHOTOS']='true'

os.environ['ENABLE_AI_HOTSPOTS']='false'
