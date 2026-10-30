# Real seller photography release — 2026-10-27

This release supersedes the illustrative 3D-product workflow. The customer and seller interfaces no longer contain the parametric model builder, synthetic model viewer or illustration library. Previously saved model records are preserved for compatibility, but are not used as product references. Synthetic demo inventory is hidden from normal catalog queries, proposals and design requests.

## Seller workflow

1. An approved, authenticated seller uploads up to six photographs of one item (JPEG, PNG or WebP; 12 MB per upload). Suggested angles are front, left, right, back, detail and angled; sellers can correct angle labels.
2. Local U2NETP/ONNX neural inference prepares transparent cutouts. It changes alpha/cropping, not the product's photographed RGB appearance. It does not generate new furniture. Metadata is stripped; images are normalized to a bounded resolution. An already transparent image can retain its supplied alpha.
3. The seller sees the original beside the cutout and checks warnings. Every photo must be reviewed and approved, with photo rights/sharing confirmation, before listing publication.
4. A selected primary cutout, dimensions, condition, price, stock and delivery location are linked to the listing. Existing listings can receive updated photo sets. Unattached photos can be deleted.
5. Original angles remain private until linked to an active, approved listing. Buyers can inspect those actual photographs. Listing dimensions and stock are not inferred from pictures.

The matting model is installed explicitly with `PYTHONPATH=backend .venv/bin/python -m app.prepare_vision`. The installer pins the model's SHA256 and download size. Install `backend/requirements-vision.txt` together with the normal requirements. Runtime requests never silently download weights. A missing model/dependency gives a configuration error; it does not substitute a fake product. The Docker configuration includes the vision dependencies and prepares the model during startup. The bundled inference model is U2NETP; cutouts must still be reviewed, especially thin legs, glass, reflections, shadows and low-contrast backgrounds.

## Room placement

Google Gemini is the primary provider; OpenAI is an optional alternative. Set `ROOM_GEMINI_API_KEY` securely and `ENABLE_AI_GENERATION=true` to activate Gemini. No provider key is present in the development runtime at verification time, so no live provider image was generated or visually accepted in this release.

The image adapters send the actual room plus approved primary and supplementary product angles. Each reference carries an explicit SKU/angle mapping so multiple views do not mean multiple items. The request limits the reference budget to 16 images and asks for original architecture, product silhouette, fabric, color, details, wear, scale, perspective, lighting and contact shadows to be preserved. Provider failures do not produce an unrelated fallback image.

A local photo layout remains available and clearly labeled. It pastes actual product cutouts with approximate scale; it is not realistic AI placement. No synthetic 3D snapshots are used in either path.

`ROOM_AI_DAILY_LIMIT` defaults to three paid AI attempts per customer in a rolling 24-hour beta window. Failed attempts count; there are no automatic paid retries. This is a safety cap, not a purchased-plan entitlement. Paid-package sales remain paused pending live quality and billing acceptance.

## Hotspots and single-item editing

The room result supports clickable product markers, a shopping list, current seller details/photographs, before-and-after comparison and manually drawn product regions. Local layouts have exact overlay coordinates. Optional AI visual grounding can suggest positions only for known SKUs above a confidence threshold. Unknown, absent, invalid and low-confidence positions are discarded. Markers and product identity still need human review; the selected shopping list is not proof that all items appeared correctly.

`ENABLE_AI_HOTSPOTS=true` enables a separate vision request after a generated image; this adds provider usage. The Gemini vision model is configurable with ROOM_GEMINI_VISION_MODEL, and OpenAI with ROOM_OPENAI_VISION_MODEL. Failed grounding leaves a usable image/list with manual marking rather than invented coordinates.

For a replacement, the customer selects one listed product, chooses an available alternative, confirms an edit rectangle and consents to provider sharing. The server checks project ownership, plan expiry, category, currency, stock, condition, coarse fit, delivery coverage and the original confirmed budget. A masked image-edit request uses the replacement's actual photographs. The resulting image is composited into the confirmed rectangle and saved losslessly, preserving pixels outside it exactly. This does not guarantee unchanged objects that overlap the edit rectangle; review its boundaries and product fidelity. The original design remains saved as a parent revision. Room originals and generated images are access-controlled.

## Verification

34 automated backend tests passed against PostgreSQL, including photo privacy/review/ownership, multi-angle reference mapping, both provider edit protocols, pixel preservation outside the rectangle, quote replacement, budget rejection, visual-grounding filtering and the AI request cap. Hosted-provider responses in those tests were simulated.

Local neural matting was also exercised on an actual Unsplash sofa photograph, and the browser check passed upload → cutout review → publication → original-photo gallery → customer project/budget/layout → clickable and manually saved hotspot → comparison, with a mobile overflow check. This fixture is a test photograph, not real seller inventory. Run `npm run check:photography` against the isolated photo-review test environment; never use its dummy merchant key on public staging.

The production frontend build passed. The Python application plus vision requirements and the frontend dependency audit reported no known vulnerabilities at scan time. These checks do not replace a live Gemini quality assessment or an independent security review.

## Remaining external acceptance

Configure the Gemini key and enable image generation, then test real customer rooms and seller angle sets for identity, wear, scale, shadows, occlusion, masked edits and per-request cost. Automated reference prompts and grounding do not guarantee SKU fidelity. Photorealistic output is not yet live-verified. Staging hosting, real email delivery, merchant payment services and commission settlement retain their documented setup requirements.
