"""Serve the compiled web app and API together for temporary local previews."""
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from .main import app

dist = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if not (dist / 'index.html').is_file():
    raise RuntimeError('Build the frontend first: cd frontend && npm run build')
app.mount('/', StaticFiles(directory=dist, html=True), name='web-preview')
