import subprocess,os,secrets,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
name='roomform-security-postgres-test'
password=secrets.token_hex(24)
env=os.environ.copy();env['POSTGRES_PASSWORD']=password
subprocess.run(['docker','run','--rm','-d','--name',name,'-p','127.0.0.1:55439:5432','-e','POSTGRES_PASSWORD','-e','POSTGRES_DB=roomform_test','postgres:16-alpine'],env=env,check=True,stdout=subprocess.DEVNULL)
try:
 for _ in range(30):
  if subprocess.run(['docker','exec',name,'pg_isready','-U','postgres'],capture_output=True).returncode==0:break
  time.sleep(1)
 env['ROOM_TEST_POSTGRES_URL']='postgresql+psycopg://postgres:'+password+'@127.0.0.1:55439/roomform_test'
 result=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','pytest','-q'],cwd=ROOT,env=env)
 raise SystemExit(result.returncode)
finally:subprocess.run(['docker','stop',name],stdout=subprocess.DEVNULL)
