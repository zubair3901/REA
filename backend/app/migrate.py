"""Additive migration for an existing v1 database. Back up before running."""
from sqlalchemy import inspect, text
from .database import Base,engine
from . import models, workspace_models

def migrate():
    Base.metadata.create_all(engine)
    columns={c['name'] for c in inspect(engine).get_columns('assets')}
    additions={'condition':"VARCHAR(20) NOT NULL DEFAULT 'new'",'delivery_location':"VARCHAR(200) NOT NULL DEFAULT ''",'delivery_radius_km':"FLOAT NOT NULL DEFAULT 50"}
    with engine.begin() as conn:
        for name,ddl in additions.items():
            if name not in columns: conn.execute(text(f'ALTER TABLE assets ADD COLUMN {name} {ddl}'))
if __name__=='__main__': migrate()
