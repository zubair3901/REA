"""Shared paths for private application data and generated media."""
from .database import DATA

MEDIA = DATA / "media"
MEDIA.mkdir(exist_ok=True)
