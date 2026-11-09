# Seller workspace

Dedicated seller route `/?page=seller`; legacy `?page=partners` remains compatible. Seller workspace renders independently of the buyer navigation and footer. Brand uses existing warm white, stone and terracotta. The supplied dashboard PDF informed task organization, not fake revenue charts, AI scores or customer profiles. Inventory statistics come from saved listings.

Inventory uses compact searchable rows and explicit edit panels. Core listing fields and prepared owned photographs can be updated. Seller product forms include grouped furniture/decor categories, style choices, and catalog metadata for brand/SKU/MPN, variants, description, colors, materials, finishes, texture, shape, placement and shipping measurements. Metadata does not itself run any AI feature. Photo preparation remains a utility for actual photographs, not synthetic product generation.

Browser location is requested only after the seller presses the location button. HTTPS or localhost and user permission are required; denial must leave manual address/location controls usable. Geolocation accuracy depends on the device and is not a delivery-address guarantee.

Roomform mediates the buyer agreement, collection and project schedule. Sellers receive fulfillment items and platform-issued receiving address/date/instructions, without buyer phone/contact or payment details. Operations assigns the schedule under Platform operations > Orders. The scheduling form does not arrange transport or make seller payouts. Existing stock reservation still occurs on order confirmation.

Catalog details endpoint: merchant-owned GET/PUT `/api/assets/{id}/catalog-details`. Core edits use PATCH `/api/assets/{id}`. Delivery assignment uses authorized PUT `/api/operator/platform/orders/{id}/delivery-plan`. Additive database tables are created with `python -m app.migrate`; back up existing data before migration. MSRP/sale metadata are reference values; the canonical listing price determines marketplace estimates.

Backend verification:52tests passed, including seller ownership, variant cycles, approved-photo replacement, schedule authorization, dispatch gating and redacted seller GET/PATCH order responses. No live email/payment/transport provider behavior was added or tested.

Frontend validation: production build passed. Chromium mock-contract test uses100 synthetic listing records to verify row browsing, closed editors, search, core and metadata saves, geolocation permission granted/denied, Escape closing and mobile overflow. Mobile rows keep product, price, stock/status and Edit visible; screenshots in ui-review/vendor are test data, not real merchant inventory or revenue. Buyer webapp navigation smoke passed. These checks do not prove real geolocation precision, actual vendor onboarding conversion or transport fulfillment.
