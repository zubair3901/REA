"""Browser request checks and lightweight per-process throttling.
Deploy the supplied reverse proxy for a second rate-limit boundary.
"""
import os
import time
from collections import deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self,app):
        super().__init__(app);self.attempts={}
    async def dispatch(self,request,call_next):
        if request.method not in ('GET','HEAD','OPTIONS') and request.url.path.startswith('/api/'):
            origin=request.headers.get('origin')
            allowed=os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')
            if origin and origin not in allowed and origin!=str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Request origin is not allowed'},status_code=403)
            length=request.headers.get('content-length','0')
            if not length.isdigit() or int(length)>16*1024*1024:
                return JSONResponse({'detail':'Request is too large; upload files individually (12 MB maximum)'},status_code=413)
        if request.method=='POST' and request.url.path.rsplit('/',1)[-1] in ('login','register','forgot-password','reset-password'):
            import hashlib
            from .database import Session
            from .workspace_models import RateLimitWindow
            from sqlalchemy import delete
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            now=int(time.time());window=now//900
            identity=request.client.host if request.client else 'unknown'
            key=hashlib.sha256((identity+':'+str(window)).encode()).hexdigest()
            with Session() as db:
                insert=pg_insert if db.bind.dialect.name=='postgresql' else sqlite_insert
                statement=insert(RateLimitWindow).values(key=key,attempts=1,expires_at=(window+1)*900)
                statement=statement.on_conflict_do_update(index_elements=['key'],set_={'attempts':RateLimitWindow.attempts+1}).returning(RateLimitWindow.attempts)
                count=db.scalar(statement)
                db.execute(delete(RateLimitWindow).where(RateLimitWindow.expires_at<now));db.commit()
            if count>30:return JSONResponse({'detail':'Too many account attempts. Try again later.'},status_code=429,headers={'Retry-After':str((window+1)*900-now)})
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if request.url.path.startswith('/api/workspace'):response.headers['Cache-Control']='no-store'
        return response
