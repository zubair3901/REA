-- Fresh PostgreSQL schema. Existing installs: python -m app.migrate
BEGIN;
CREATE TABLE sellers (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	active BOOLEAN NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE designs (
	id VARCHAR(36) NOT NULL,
	style VARCHAR(80) NOT NULL,
	image_url VARCHAR(500) NOT NULL,
	render_mode VARCHAR(40) NOT NULL,
	quote JSON NOT NULL,
	placements JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE design_plans (
	id VARCHAR(36) NOT NULL,
	parameters JSON NOT NULL,
	asset_ids JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE assets (
	id VARCHAR(36) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	category VARCHAR(80) NOT NULL,
	style VARCHAR(80) NOT NULL,
	price NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	width_cm FLOAT NOT NULL,
	height_cm FLOAT NOT NULL,
	depth_cm FLOAT NOT NULL,
	image_url VARCHAR(500) NOT NULL,
	latitude FLOAT NOT NULL,
	longitude FLOAT NOT NULL,
	stock INTEGER NOT NULL,
	delivery_days INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	condition VARCHAR(20) DEFAULT 'new' NOT NULL,
	delivery_location VARCHAR(200) DEFAULT '' NOT NULL,
	delivery_radius_km FLOAT DEFAULT '50' NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id)
);

CREATE INDEX ix_assets_seller_id ON assets (seller_id);

CREATE TABLE leads (
	id VARCHAR(36) NOT NULL,
	design_id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	email VARCHAR(254) NOT NULL,
	phone VARCHAR(40) NOT NULL,
	consent BOOLEAN NOT NULL,
	status VARCHAR(40) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(design_id) REFERENCES designs (id)
);

CREATE INDEX ix_leads_design_id ON leads (design_id);

CREATE TABLE seller_accounts (
	seller_id VARCHAR(36) NOT NULL,
	email VARCHAR(254) NOT NULL,
	password_hash VARCHAR(300) NOT NULL,
	kind VARCHAR(20) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (seller_id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	UNIQUE (email)
);

CREATE TABLE seller_sessions (
	token_hash VARCHAR(64) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(seller_id) REFERENCES sellers (id)
);

CREATE INDEX ix_seller_sessions_seller_id ON seller_sessions (seller_id);

CREATE TABLE outbox (
	id VARCHAR(36) NOT NULL,
	lead_id VARCHAR(36) NOT NULL,
	payload JSON NOT NULL,
	attempts INTEGER NOT NULL,
	delivered BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (lead_id),
	FOREIGN KEY(lead_id) REFERENCES leads (id)
);
COMMIT;
