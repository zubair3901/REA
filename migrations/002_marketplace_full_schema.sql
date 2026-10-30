-- Fresh PostgreSQL schema only. Use app.migrate for an existing database.


CREATE TABLE administrators (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(254) NOT NULL,
	password_hash VARCHAR(300) NOT NULL,
	totp_secret VARCHAR(80) NOT NULL,
	last_counter INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (email)
)

;


CREATE TABLE audit_events (
	id VARCHAR(36) NOT NULL,
	actor VARCHAR(80) NOT NULL,
	action VARCHAR(80) NOT NULL,
	target_id VARCHAR(36) NOT NULL,
	details JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE customers (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(254) NOT NULL,
	name VARCHAR(160) NOT NULL,
	password_hash VARCHAR(300) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (email)
)

;


CREATE TABLE design_plans (
	id VARCHAR(36) NOT NULL,
	parameters JSON NOT NULL,
	asset_ids JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE designs (
	id VARCHAR(36) NOT NULL,
	style VARCHAR(80) NOT NULL,
	image_url VARCHAR(500) NOT NULL,
	render_mode VARCHAR(40) NOT NULL,
	quote JSON NOT NULL,
	placements JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE mail_queue (
	id VARCHAR(36) NOT NULL,
	recipient VARCHAR(254) NOT NULL,
	subject VARCHAR(200) NOT NULL,
	body VARCHAR(5000) NOT NULL,
	attempts INTEGER NOT NULL,
	status VARCHAR(20) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE rate_limit_windows (
	key VARCHAR(64) NOT NULL,
	attempts INTEGER NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (key)
)

;

CREATE INDEX ix_rate_limit_windows_expires_at ON rate_limit_windows (expires_at);


CREATE TABLE sellers (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	active BOOLEAN NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE administrator_sessions (
	token_hash VARCHAR(64) NOT NULL,
	administrator_id VARCHAR(36) NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(administrator_id) REFERENCES administrators (id)
)

;


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
)

;

CREATE INDEX ix_assets_seller_id ON assets (seller_id);


CREATE TABLE customer_sessions (
	token_hash VARCHAR(64) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;

CREATE INDEX ix_customer_sessions_customer_id ON customer_sessions (customer_id);


CREATE TABLE design_scenes (
	design_id VARCHAR(36) NOT NULL,
	original_file VARCHAR(200) NOT NULL,
	parameters JSON NOT NULL,
	hotspots JSON NOT NULL,
	parent_id VARCHAR(36),
	PRIMARY KEY (design_id),
	FOREIGN KEY(design_id) REFERENCES designs (id),
	FOREIGN KEY(parent_id) REFERENCES designs (id)
)

;


CREATE TABLE email_verifications (
	customer_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at INTEGER NOT NULL,
	verified_at INTEGER NOT NULL,
	PRIMARY KEY (customer_id),
	FOREIGN KEY(customer_id) REFERENCES customers (id),
	UNIQUE (token_hash)
)

;


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
)

;

CREATE INDEX ix_leads_design_id ON leads (design_id);


CREATE TABLE organizations (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	plan VARCHAR(20) NOT NULL,
	seats INTEGER NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(owner_id) REFERENCES customers (id)
)

;


CREATE TABLE password_resets (
	token_hash VARCHAR(64) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;

CREATE INDEX ix_password_resets_customer_id ON password_resets (customer_id);


CREATE TABLE professionals (
	id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	name VARCHAR(160) NOT NULL,
	trade VARCHAR(60) NOT NULL,
	location VARCHAR(200) NOT NULL,
	description VARCHAR(2000) NOT NULL,
	phone VARCHAR(40) NOT NULL,
	daily_rate NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	status VARCHAR(20) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (customer_id),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;


CREATE TABLE seller_accounts (
	seller_id VARCHAR(36) NOT NULL,
	email VARCHAR(254) NOT NULL,
	password_hash VARCHAR(300) NOT NULL,
	kind VARCHAR(20) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (seller_id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	UNIQUE (email)
)

;


CREATE TABLE seller_email_verifications (
	seller_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at INTEGER NOT NULL,
	verified_at INTEGER NOT NULL,
	PRIMARY KEY (seller_id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	UNIQUE (token_hash)
)

;


CREATE TABLE seller_sessions (
	token_hash VARCHAR(64) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	expires_at INTEGER NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(seller_id) REFERENCES sellers (id)
)

;

CREATE INDEX ix_seller_sessions_seller_id ON seller_sessions (seller_id);


CREATE TABLE memberships (
	id VARCHAR(36) NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (organization_id, customer_id),
	FOREIGN KEY(organization_id) REFERENCES organizations (id),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;

CREATE INDEX ix_memberships_customer_id ON memberships (customer_id);

CREATE INDEX ix_memberships_organization_id ON memberships (organization_id);


CREATE TABLE outbox (
	id VARCHAR(36) NOT NULL,
	lead_id VARCHAR(36) NOT NULL,
	payload JSON NOT NULL,
	attempts INTEGER NOT NULL,
	delivered BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (lead_id),
	FOREIGN KEY(lead_id) REFERENCES leads (id)
)

;


CREATE TABLE product_models (
	id VARCHAR(36) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	asset_id VARCHAR(36),
	name VARCHAR(160) NOT NULL,
	specifications JSON NOT NULL,
	thumbnail_url VARCHAR(500) NOT NULL,
	model_url VARCHAR(500) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	UNIQUE (asset_id),
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;

CREATE INDEX ix_product_models_seller_id ON product_models (seller_id);


CREATE TABLE product_photos (
	id VARCHAR(36) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	asset_id VARCHAR(36),
	angle VARCHAR(30) NOT NULL,
	original_file VARCHAR(200) NOT NULL,
	cutout_url VARCHAR(500) NOT NULL,
	quality JSON NOT NULL,
	approved INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;

CREATE INDEX ix_product_photos_asset_id ON product_photos (asset_id);

CREATE INDEX ix_product_photos_seller_id ON product_photos (seller_id);


CREATE TABLE projects (
	id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	organization_id VARCHAR(36),
	name VARCHAR(160) NOT NULL,
	location VARCHAR(200) NOT NULL,
	budget NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	preference VARCHAR(20) NOT NULL,
	status VARCHAR(30) NOT NULL,
	credits INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES customers (id),
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)

;

CREATE INDEX ix_projects_customer_id ON projects (customer_id);


CREATE TABLE ai_usage (
	id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	operation VARCHAR(30) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES customers (id),
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

CREATE INDEX ix_ai_usage_project_id ON ai_usage (project_id);

CREATE INDEX ix_ai_usage_customer_id ON ai_usage (customer_id);


CREATE TABLE orders (
	id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	seller_id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	items JSON NOT NULL,
	total NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	address VARCHAR(500) NOT NULL,
	phone VARCHAR(40) NOT NULL,
	status VARCHAR(30) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(project_id) REFERENCES projects (id),
	FOREIGN KEY(seller_id) REFERENCES sellers (id),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;

CREATE INDEX ix_orders_seller_id ON orders (seller_id);

CREATE INDEX ix_orders_project_id ON orders (project_id);


CREATE TABLE payment_requests (
	id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	customer_id VARCHAR(36) NOT NULL,
	package VARCHAR(20) NOT NULL,
	amount NUMERIC(12, 2) NOT NULL,
	credits INTEGER NOT NULL,
	status VARCHAR(20) NOT NULL,
	reference VARCHAR(200) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(project_id) REFERENCES projects (id),
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;

CREATE INDEX ix_payment_requests_project_id ON payment_requests (project_id);


CREATE TABLE project_designs (
	design_id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (design_id),
	FOREIGN KEY(design_id) REFERENCES designs (id),
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

CREATE INDEX ix_project_designs_project_id ON project_designs (project_id);


CREATE TABLE service_requests (
	id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	professional_id VARCHAR(36),
	kind VARCHAR(30) NOT NULL,
	brief VARCHAR(2000) NOT NULL,
	phone VARCHAR(40) NOT NULL,
	preferred_date VARCHAR(30) NOT NULL,
	status VARCHAR(30) NOT NULL,
	quoted_amount NUMERIC(12, 2),
	currency VARCHAR(3) NOT NULL,
	response VARCHAR(2000) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(project_id) REFERENCES projects (id),
	FOREIGN KEY(professional_id) REFERENCES professionals (id)
)

;

CREATE INDEX ix_service_requests_project_id ON service_requests (project_id);


CREATE TABLE gateway_events (
	id VARCHAR(200) NOT NULL,
	payment_id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(payment_id) REFERENCES payment_requests (id)
)

;


CREATE TABLE order_commissions (
	order_id VARCHAR(36) NOT NULL,
	rate_percent NUMERIC(5, 2) NOT NULL,
	amount NUMERIC(12, 2) NOT NULL,
	seller_net NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	status VARCHAR(30) NOT NULL,
	PRIMARY KEY (order_id),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)

;
