"""Create/reset a disposable seller in the local preview database only."""
import os
from pathlib import Path
import secrets
import sys
from uuid import uuid4
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
preview = root / 'backend' / 'preview-data'
# Deliberately ignore externally configured databases: this helper only touches preview data.
os.environ['DATA_DIR'] = str(preview)
os.environ['DATABASE_URL'] = 'sqlite:///' + str(preview / 'marketplace.db')
from sqlalchemy import select
from app.database import Session
from app.migrate import migrate
from app.models import Seller, SellerAccount, Asset
from app.accounts import password_hash
from app.workspace_models import AssetFulfillment
from PIL import Image
migrate()
email = 'seller.demo@example.com'
password = secrets.token_urlsafe(18)
with Session() as db:
    account = db.scalar(select(SellerAccount).where(SellerAccount.email == email))
    if account:
        seller = db.get(Seller, account.seller_id)
        account.password_hash = password_hash(password)
    else:
        seller = Seller(id=str(uuid4()), name='Demo furniture studio', active=True)
        db.add(seller); db.flush()
        db.add(SellerAccount(seller_id=seller.id, email=email, password_hash=password_hash(password), kind='merchant'))
    seller.active = True
    if not db.scalar(select(Asset).where(Asset.seller_id == seller.id)):
        fixture = root / 'frontend/tests/fixtures/product-sofa.jpg'
        if fixture.exists():
            media = preview / 'media'; media.mkdir(exist_ok=True)
            filename = 'demo-seller-sofa.png'
            with Image.open(fixture) as image: image.convert('RGB').save(media / filename)
            asset = Asset(id=str(uuid4()), seller_id=seller.id, name='DEMO — photographic sofa sample', category='sofa', style='modern', price=850, currency='USD', width_cm=220, height_cm=85, depth_cm=90, image_url='/media/' + filename, latitude=24.86, longitude=67.00, stock=3, delivery_days=5, active=False, condition='good', delivery_location='Karachi', delivery_radius_km=30)
            db.add(asset); db.flush()
            db.add(AssetFulfillment(asset_id=asset.id, ready_min_days=2, ready_max_days=4, delivery_min_days=1, delivery_max_days=3))
    db.commit()
print('Local preview seller created. Payments/AI remain controlled by preview settings.')
print('Open: http://localhost:8080/?page=partners')
print('Choose Sign in (not Register as a seller).')
print('Email:', email)
print('Password:', password)
print('Sample listing is hidden from shopping; it is a photographic fixture, not real stock.')
print('Run this helper again to reset the demo password.')
