"""System routes: HTTP adapters for a single application concern."""
import os
from .generation import models
from fastapi import APIRouter

router = APIRouter()

@router.get('/health')
def health(): return {'status':'ok','ai_generation_enabled':os.getenv('ENABLE_AI_GENERATION','false')=='true' and any(m['available'] for m in models() if m['id']!='composite')}

@router.get('/api/models')
def available_models():
    return [{**m, **({'available':False,'reason':'AI placement is disabled by the operator'} if m['id']!='composite' and os.getenv('ENABLE_AI_GENERATION','false')!='true' else {})} for m in models()]

@router.get('/api/placement/capabilities')
def placement_capabilities():
    from .protected_placement import capabilities
    return capabilities()
