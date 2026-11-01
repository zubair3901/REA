# Measured product-protected placement beta

This is an additional rendering path, not a claim of production photorealism.
Existing local layouts and reference-guided Gemini/OpenAI generation still work.
New code is tested with simulated service responses; no live inference was run.

## What it does

1. Verify authenticated project ownership, active/approved seller photographs,
   inventory, condition preference, currency, budget, delivery and room settings.
2. Require a customer-confirmed **measured floor rectangle**: four image corners
   (far-left, far-right, near-right, near-left), real width/depth in cm, one SKU
   position and available photographed view per item. No absolute scale is
   invented from one photo. Qualitative angle labels are not calibrated yaw.
3. Reject unsupported views, clipped products, overlapping solid footprints,
   mostly hidden products and geometrically invalid calibrations before paid work.
4. Reserve three beta attempt slots atomically before a fresh workflow, or one
   for cached-room reuse/replacement. Failed and unused stage reservations count;
   these are spend safeguards, not paid image credits or actual charges.
5. Call an operator-configured **grounded object detector + segmentation service**.
   SAM 2 can refine prompted regions, but cannot independently text-detect sofas.
   This repository implements the service client and validation contract; it does
   not install or host Grounding DINO/SAM 2 weights or a GPU inference server.
6. Validate detection confidence, classes, normalized boxes, mask dimensions and
   cleanup area. Stop on uncertainty or masks outside confident detections.
7. Use Gemini/OpenAI to fill removal holes. Locally restore every pixel outside
   the validated mask. Foreground retention masks take precedence over removal.
8. Map the measured rectangle with a projective homography. Uniformly scale
   compatible photographs of solid furniture without projective deformation.
   Rugs require an approved **top-down** view and use a floor homography.
   Approximate angled-view scale is not a guaranteed physical fit.
9. Add local contact shadows in the selected light direction; layer products by
   floor depth. Optional binary foreground masks retain original room objects.
10. Ask the image provider to harmonize contact/shadow surroundings. Locally
    discard changes outside that narrow ring and restore every non-transparent
    product pixel from the staged composite. No whole-image generative polish.
11. Verify the protected pixels, save a lossless PNG, attach exact overlay boxes
    to actual SKUs, persist the private original and cleanup cache, and return the
    quote and consultation/order actions. No mandatory staff image-review queue.

There is no `denoising_strength=0.18` guarantee: Gemini/OpenAI's current adapters
have no such parameter. Protection comes from local masks and hard compositing.
Checks prove particular pixel/geometry invariants, not visual correctness, seller
truthfulness, camera-angle compatibility, buildability, or exact physical fit.

## Configuration

Use secure server environment settings; never VITE variables:

```
ENABLE_AI_GENERATION=true
ENABLE_PROTECTED_PLACEMENT=true
ROOM_PRIMARY_PROVIDER=gemini
ROOM_GEMINI_API_KEY=<securely bound, never committed>
ROOM_PERCEPTION_URL=https://your-grounded-segmentation-service.example/segment
ROOM_PERCEPTION_API_KEY=<securely bound if required>
```

The perception service URL is operator-controlled, HTTPS-only, has no embedded
credentials and does not follow redirects. No client-supplied endpoint is accepted.
The capability endpoint exposes readiness flags, not URLs or secrets.

### Perception service contract

POST JSON, with optional server-side Bearer authentication:

```json
{
  "task": "grounded_segmentation",
  "image_base64": "<PNG room at working dimensions>",
  "image_width": 1280,
  "image_height": 960,
  "classes": ["bed", "chair", "couch", "rug", "sofa", "table"],
  "mask_convention": "white_remove_black_preserve"
}
```

Return JSON (boxes are normalized x/y/width/height):

```json
{
  "mask_base64": "<binary mask image, same dimensions as the room>",
  "detections": [
    {"label": "sofa", "confidence": 0.95, "box": [0.1, 0.4, 0.4, 0.3]}
  ]
}
```

White means removal; black means preserve. Confidence must be at least 0.8.
An already empty room returns a completely black mask and no detections. Masks
covering over 60% of the room or extending outside detection boxes are rejected.
Thresholds need evaluation on real rooms. This is a **custom adapter contract**,
not a claim that a vendor's hosted SAM endpoint accepts this exact schema.

### App requests

`POST /api/designs` retains its existing multipart fields and adds:

- `pipeline=protected`
- `placement_spec` JSON: `floor_quad`, `floor_width_cm`, `floor_depth_cm`,
  `measurement_confirmed: true`, and `placements` (`asset_id`, `u`, `v`, `view`).
  `u` runs left→right and `v` far→near across the measured rectangle. Position is
  the item's front-edge center. Valid views are front/left/right/angled/top.
- Optional `light_dx`, `light_dy`, `occlusion_mask_base64` and `reuse_design_id`.

The room working image fits within 1280×960 preserving aspect. A foreground mask
must match that working size and use white for retained foreground, black elsewhere.
The frontend supplies floor-corner controls, dimensions, view/position controls,
light direction and an optional foreground-mask upload.

`POST /api/designs/{id}/protected-replace` accepts `old_asset_id`, `new_asset_id`,
`view` and `ai_consent: true`. It reuses the authorized project's cached empty room,
checks the current quote/inventory/footprints again, recomposites actual photos and
reserves only one harmonization attempt. Existing versions remain saved. Generic
region-redraw replacement is rejected for protected designs so it cannot undo the
product-fidelity contract.

## Storage, security and limits

Cleanup images and optional foreground masks are under private
`DATA_DIR/protected-stages/<server-design-id>/`, outside static media. New cache
directories/files use 0700/0600. Reuse is restricted to the authorized project and
matching input-room fingerprint/provider. No global cross-customer image cache.
Generated PNGs follow the same project authorization as JPGs. Seller cutouts remain
public only under the existing approved-listing rules. Back up media and database
together; add business retention/purge rules before public launch.

The endpoint remains synchronous and has bounded external timeouts, no automatic
paid retries, and a daily database quota guard. A durable queue, job recovery,
provider billing reconciliation and production load testing are still needed for
large-scale operation. Camera/depth inference, automatic high-quality layout and
photorealistic shadow evaluation remain future validation/integration work.
