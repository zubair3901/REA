"""Persistent customer, team, service and commerce records."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from .models import now

class Customer(Base):
    __tablename__ = 'customers'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(300))

class CustomerSession(Base):
    __tablename__ = 'customer_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), index=True)
    expires_at: Mapped[int] = mapped_column(Integer)

class Organization(Base):
    __tablename__ = 'organizations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    owner_id: Mapped[str] = mapped_column(ForeignKey('customers.id'))
    plan: Mapped[str] = mapped_column(String(20), default='basic')
    seats: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[int] = mapped_column(Integer, default=0)

class Membership(Base):
    __tablename__ = 'memberships'
    __table_args__ = (UniqueConstraint('organization_id', 'customer_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), index=True)

class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), index=True)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey('organizations.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(200))
    budget: Mapped[Decimal] = mapped_column(Numeric(12,2))
    currency: Mapped[str] = mapped_column(String(3))
    preference: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default='planning')
    credits: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ProjectDesign(Base):
    __tablename__ = 'project_designs'
    design_id: Mapped[str] = mapped_column(ForeignKey('designs.id'), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)

class PaymentRequest(Base):
    __tablename__ = 'payment_requests'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'))
    package: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2))
    credits: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='awaiting_payment')
    reference: Mapped[str] = mapped_column(String(200), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Professional(Base):
    __tablename__ = 'professionals'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    trade: Mapped[str] = mapped_column(String(60))
    location: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000))
    phone: Mapped[str] = mapped_column(String(40))
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(12,2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20), default='pending')

class ServiceRequest(Base):
    __tablename__ = 'service_requests'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    professional_id: Mapped[str | None] = mapped_column(ForeignKey('professionals.id'), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))
    brief: Mapped[str] = mapped_column(String(2000))
    phone: Mapped[str] = mapped_column(String(40))
    preferred_date: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default='requested')
    quoted_amount: Mapped[Decimal | None] = mapped_column(Numeric(12,2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    response: Mapped[str] = mapped_column(String(2000), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    seller_id: Mapped[str] = mapped_column(ForeignKey('sellers.id'), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'))
    items: Mapped[list] = mapped_column(JSON)
    total: Mapped[Decimal] = mapped_column(Numeric(12,2))
    currency: Mapped[str] = mapped_column(String(3))
    address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default='requested')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class PasswordReset(Base):
    __tablename__ = 'password_resets'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), index=True)
    expires_at: Mapped[int] = mapped_column(Integer)

class MailQueue(Base):
    __tablename__ = 'mail_queue'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipient: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(5000))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Administrator(Base):
    __tablename__='administrators'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    email: Mapped[str]=mapped_column(String(254),unique=True)
    password_hash: Mapped[str]=mapped_column(String(300))
    totp_secret: Mapped[str]=mapped_column(String(80))
    last_counter: Mapped[int]=mapped_column(Integer,default=-1)

class AdministratorSession(Base):
    __tablename__='administrator_sessions'
    token_hash: Mapped[str]=mapped_column(String(64),primary_key=True)
    administrator_id: Mapped[str]=mapped_column(ForeignKey('administrators.id'))
    expires_at: Mapped[int]=mapped_column(Integer)

class EmailVerification(Base):
    __tablename__='email_verifications'
    customer_id: Mapped[str]=mapped_column(ForeignKey('customers.id'),primary_key=True)
    token_hash: Mapped[str]=mapped_column(String(64),unique=True)
    expires_at: Mapped[int]=mapped_column(Integer)
    verified_at: Mapped[int]=mapped_column(Integer,default=0)

class GatewayEvent(Base):
    __tablename__='gateway_events'
    id: Mapped[str]=mapped_column(String(200),primary_key=True)
    payment_id: Mapped[str]=mapped_column(ForeignKey('payment_requests.id'))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class RateLimitWindow(Base):
    __tablename__='rate_limit_windows'
    key: Mapped[str]=mapped_column(String(64),primary_key=True)
    attempts: Mapped[int]=mapped_column(Integer)
    expires_at: Mapped[int]=mapped_column(Integer,index=True)

class SellerEmailVerification(Base):
    __tablename__='seller_email_verifications'
    seller_id: Mapped[str]=mapped_column(ForeignKey('sellers.id'),primary_key=True)
    token_hash: Mapped[str]=mapped_column(String(64),unique=True)
    expires_at: Mapped[int]=mapped_column(Integer)
    verified_at: Mapped[int]=mapped_column(Integer,default=0)

class ProductModel(Base):
    __tablename__='product_models'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    seller_id: Mapped[str]=mapped_column(ForeignKey('sellers.id'),index=True)
    asset_id: Mapped[str | None]=mapped_column(ForeignKey('assets.id'),unique=True,nullable=True)
    name: Mapped[str]=mapped_column(String(160))
    specifications: Mapped[dict]=mapped_column(JSON)
    thumbnail_url: Mapped[str]=mapped_column(String(500))
    model_url: Mapped[str]=mapped_column(String(500))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class OrderCommission(Base):
    __tablename__='order_commissions'
    order_id: Mapped[str]=mapped_column(ForeignKey('orders.id'),primary_key=True)
    rate_percent: Mapped[Decimal]=mapped_column(Numeric(5,2))
    amount: Mapped[Decimal]=mapped_column(Numeric(12,2))
    seller_net: Mapped[Decimal]=mapped_column(Numeric(12,2))
    currency: Mapped[str]=mapped_column(String(3))
    status: Mapped[str]=mapped_column(String(30),default='uncollected')

class ProductPhoto(Base):
    __tablename__='product_photos'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    seller_id: Mapped[str]=mapped_column(ForeignKey('sellers.id'),index=True)
    asset_id: Mapped[str | None]=mapped_column(ForeignKey('assets.id'),nullable=True,index=True)
    angle: Mapped[str]=mapped_column(String(30))
    original_file: Mapped[str]=mapped_column(String(200))
    cutout_url: Mapped[str]=mapped_column(String(500))
    quality: Mapped[dict]=mapped_column(JSON)
    approved: Mapped[int]=mapped_column(Integer,default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class DesignScene(Base):
    __tablename__='design_scenes'
    design_id: Mapped[str]=mapped_column(ForeignKey('designs.id'),primary_key=True)
    original_file: Mapped[str]=mapped_column(String(200))
    parameters: Mapped[dict]=mapped_column(JSON)
    hotspots: Mapped[list]=mapped_column(JSON,default=list)
    parent_id: Mapped[str | None]=mapped_column(ForeignKey('designs.id'),nullable=True)

class AIUsage(Base):
    __tablename__='ai_usage'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    customer_id: Mapped[str]=mapped_column(ForeignKey('customers.id'),index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey('projects.id'),index=True)
    operation: Mapped[str]=mapped_column(String(30))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AssetFulfillment(Base):
    __tablename__ = 'asset_fulfillment'
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), primary_key=True)
    ready_min_days: Mapped[int] = mapped_column(Integer)
    ready_max_days: Mapped[int] = mapped_column(Integer)
    delivery_min_days: Mapped[int] = mapped_column(Integer)
    delivery_max_days: Mapped[int] = mapped_column(Integer)

class FinalizationBooking(Base):
    __tablename__ = 'finalization_bookings'
    __table_args__ = (UniqueConstraint('customer_id', 'idempotency_key'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'))
    design_id: Mapped[str] = mapped_column(ForeignKey('designs.id'))
    idempotency_key: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    snapshot: Mapped[dict] = mapped_column(JSON)
    pdf: Mapped[str] = mapped_column(String(100))
    mail_id: Mapped[str | None] = mapped_column(ForeignKey('mail_queue.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
