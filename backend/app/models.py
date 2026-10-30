from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def now(): return datetime.now(timezone.utc)
class Seller(Base):
    __tablename__ = 'sellers'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Asset(Base):
    __tablename__ = 'assets'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    seller_id: Mapped[str] = mapped_column(ForeignKey('sellers.id'), index=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80))
    style: Mapped[str] = mapped_column(String(80))
    price: Mapped[Decimal] = mapped_column(Numeric(12,2))
    currency: Mapped[str] = mapped_column(String(3))
    width_cm: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)
    depth_cm: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer)
    delivery_days: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    condition: Mapped[str] = mapped_column(String(20), default='new', server_default='new')
    delivery_location: Mapped[str] = mapped_column(String(200), default='', server_default='')
    delivery_radius_km: Mapped[float] = mapped_column(Float, default=50, server_default='50')

class Design(Base):
    __tablename__ = 'designs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    style: Mapped[str] = mapped_column(String(80))
    image_url: Mapped[str] = mapped_column(String(500))
    render_mode: Mapped[str] = mapped_column(String(40))
    quote: Mapped[dict] = mapped_column(JSON)
    placements: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Lead(Base):
    __tablename__ = 'leads'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    design_id: Mapped[str] = mapped_column(ForeignKey('designs.id'), index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(40))
    consent: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(40), default='pending_consultation')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Outbox(Base):
    __tablename__ = 'outbox'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey('leads.id'), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)

class SellerAccount(Base):
    __tablename__ = 'seller_accounts'
    seller_id: Mapped[str] = mapped_column(ForeignKey('sellers.id'), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SellerSession(Base):
    __tablename__ = 'seller_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_id: Mapped[str] = mapped_column(ForeignKey('sellers.id'), index=True)
    expires_at: Mapped[int] = mapped_column(Integer)

class DesignPlan(Base):
    __tablename__ = 'design_plans'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parameters: Mapped[dict] = mapped_column(JSON)
    asset_ids: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
