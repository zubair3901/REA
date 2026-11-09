"""Application composition root: lifecycle, middleware and API router registration.

Business validation lives in schemas/services; HTTP endpoints live in concern-specific
route modules. `app` remains the ASGI entrypoint used by uvicorn and preview.py.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .security import SecurityMiddleware
# Compatibility export for existing scripts; new code imports app.storage directly.
from .storage import MEDIA
from .finalization import router as finalization_router
from .accounts import router as account_router
from .planning import router as planning_router
from .operations import router as operations_router
from .workspace import router as workspace_router
from .recovery import router as recovery_router
from .admin_auth import router as admin_auth_router
from .verification import router as verification_router
from .payments import router as payments_router
from .seller_verification import router as seller_verification_router
from .commerce import router as commerce_router
from .scene_routes import router as scene_router
from .workspace_operations import router as platform_operator_router
from .vendor_catalog import router as vendor_catalog_router
from .system_routes import router as system_routes_router
from .catalog_routes import router as catalog_routes_router
from .design_routes import router as design_routes_router
from .lead_routes import router as lead_routes_router
from .media_routes import router as media_routes_router
from .seller_order_routes import router as seller_order_routes_router
from .product_model_routes import router as product_model_routes_router
from .photo_routes import router as photo_routes_router

@asynccontextmanager
async def lifespan(app):
    if os.getenv("AUTO_CREATE_SCHEMA", "true") == "true":
        Base.metadata.create_all(engine)
    yield


def create_app():
    """Assemble the API without coupling feature modules to the ASGI entrypoint."""
    application = FastAPI(title="Roomform Marketplace", version="1.0.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Merchant-Key", "X-Operator-Key"],
    )
    application.add_middleware(SecurityMiddleware)
    for router in (
        finalization_router,
        account_router,
        planning_router,
        operations_router,
        workspace_router,
        recovery_router,
        admin_auth_router,
        verification_router,
        payments_router,
        seller_verification_router,
        commerce_router,
        scene_router,
        platform_operator_router,
        vendor_catalog_router,
        system_routes_router,
        catalog_routes_router,
        design_routes_router,
        lead_routes_router,
        media_routes_router,
        seller_order_routes_router,
        product_model_routes_router,
        photo_routes_router,
    ):
        application.include_router(router)
    return application


app = create_app()
