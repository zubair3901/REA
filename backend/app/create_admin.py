"""Run interactively on a trusted server. Provision the QR URI privately."""
import getpass,pyotp
from uuid import uuid4
from .database import Session
from .accounts import password_hash
from .workspace_models import Administrator
if __name__=='__main__':
    email=input('Administrator email: ').strip().lower()
    password=getpass.getpass('Password (12+ characters): ')
    if len(password)<12:raise SystemExit('Password too short')
    secret=pyotp.random_base32()
    print('Add this URI to your authenticator privately:',pyotp.TOTP(secret).provisioning_uri(email,issuer_name='Roomform'))
    code=input('Confirm current authenticator code: ').strip()
    if not pyotp.TOTP(secret).verify(code):raise SystemExit('Authenticator verification failed')
    with Session() as db:
        db.add(Administrator(id=str(uuid4()),email=email,password_hash=password_hash(password),totp_secret=secret));db.commit()
    print('Administrator created.')
