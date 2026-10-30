# Roomform product fidelity and API handoff

Recorded: 27 October 2026. This document captures the user's current requirements and the provider research discussed in voice. It supersedes the earlier generic 3D furniture direction.

## Core business requirement

The actual item offered by a seller must remain recognizable and accurately represented in the customer's room visualization. A sofa's arms, legs, silhouette, fabric, pattern, construction, condition and visible wear must not silently change. A visually attractive substitute is not an acceptable representation of the purchasable SKU. Dimensions, stock, prices and delivery coverage come from verified inventory records and software rules, not image-model guesses.

The platform should operate automatically, 24/7. There must be no mandatory employee approval queue before results reach customers. An individual seller should be able to begin with one clear photograph; multiple angles, video or manual model creation must not be mandatory for ordinary listings. Sellers do not need to provide a transparent background: the platform prepares cutouts. Additional photographs can be requested selectively when an input is insufficient.

## Essential distinction

A generated image that resembles a product is not proof that it preserves the exact product. Reference prompts, AI confidence, embedding similarity and an AI judge are not guarantees of SKU identity. We must not claim that an existing provider already solves this on our inventory without testing it.

For compatible viewpoints, the recommended identity-preserving path retains the photographed object as a protected image layer, with controlled placement, scale, occlusion and surrounding contact shadows. Color management and any relighting must be evaluated for material/color drift; changing illumination can legitimately change pixel appearance, so literal RGB equality is not the same as material fidelity. Extreme perspective changes cannot be achieved reliably by simply warping a cutout.

If the desired view needs unseen product surfaces, the automatic system should choose a compatible placement, request an optional additional photo, or decline that view. It should not silently invent the missing surfaces and present them as verified. A single product photo does not establish unseen geometry; a room photo alone does not establish exact physical scale. Product and room measurements remain necessary for strong fit claims.

## Provider map and official sources

### Google — Gemini

Role: room understanding, layout suggestions, optional image editing and automatic visual checks. User-selected primary provider for the current implementation.

Documentation: https://ai.google.dev/gemini-api/docs/image-generation

Current application integration: Gemini image-edit requests use `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`. Model selection is configurable. Current default image model is `gemini-2.5-flash-image`; model availability must be verified with the configured account. Vision grounding uses a separately configurable vision model.

Environment: `ROOM_GEMINI_API_KEY`, `ROOM_GEMINI_MODEL`, `ROOM_GEMINI_VISION_MODEL`, `ROOM_PRIMARY_PROVIDER=gemini`, `ENABLE_AI_GENERATION=true`.

### OpenAI — GPT Image

Role: alternative image generation/editing provider and optional visual grounding.

Documentation: https://platform.openai.com/docs/guides/image-generation

Current application integration: image edits at `https://api.openai.com/v1/images/edits`, with product references and a mask for single-item edits. Model selection is configurable. The current default is `gpt-image-1.5`; account/model availability requires verification.

Environment: `ROOM_OPENAI_API_KEY`, `ROOM_OPENAI_MODEL`, `ROOM_OPENAI_VISION_MODEL`.

### BRIA — independent visual AI company

Most directly relevant specialized API found during research: Product Integration.

Official endpoint documentation: https://docs.bria.ai/product-shot-editing/products/product-integrate

Best practices: https://docs.bria.ai/product-shots-best-practices

Product cutout: https://docs.bria.ai/product-shot-editing/products/product-cutout-v2

The documentation describes integration of one or more product images into a supplied scene using explicit x/y/width/height coordinates, with matching lighting and perspective. Coordinates refer to the tightly cropped product; developers must preserve its appropriate aspect ratio. BRIA also documents automatic placement planning and batch QA using vision models alongside its APIs.

Developer base URL documented during research: `https://engine.prod.bria-api.com`; authentication uses `api_token`. Product Integration is documented under the v2 product editing family as `/v2/image/edit/product/integrate`; confirm the complete endpoint contract and account availability before implementation. No BRIA credentials or paid tests were used.

Important: the product-integration documentation is not a demonstrated guarantee of unchanged SKU details. A background-generation mode's product-preservation claims must not be assumed to apply identically to the integration endpoint.

### Black Forest Labs — FLUX

An independent provider, not Google or OpenAI.

Multi-reference editing: https://docs.bfl.ml/guides/prompting_editing_multi_reference

FLUX 3 editing: https://docs.bfl.ml/flux_3/flux3_image_layout

FLUX.2 editing: https://docs.bfl.ml/flux_2/flux2_image_editing

Retrieved FLUX 3 documentation describes up to ten reference images, source/target bounding boxes and anchors for scene elements. It includes product-to-room examples. Retrieved FLUX.2 documentation explicitly describes furniture combination and distinguishes eight API references from ten in its playground.

Documented FLUX 3 image endpoint: `https://api.bfl.ai/v1/flux-3-image`, with `x-key` authentication. Treat the hosted API terms separately from any open-weight model license. No FLUX integration or paid benchmark has been performed in this project.

### Photoroom — independent product-photography service

Potential role: cutout preparation, uncertainty estimates, product relighting and shadows.

Relighting: https://docs.photoroom.com/image-editing-api-plus-plan/ai-relight

Cutout uncertainty: https://docs.photoroom.com/image-editing-api-plus-plan/uncertainty-score

Pricing documentation: https://docs.photoroom.com/image-editing-api-plus-plan/pricing

The API documents `lighting.mode=ai.preserve-hue-and-saturation`. Its cutout uncertainty header is `x-uncertainty-score`: zero means confident, one means uncertain and -1 can indicate unavailable confidence. This score concerns segmentation, not final furniture identity or physical fit, and the provider warns it can change across model versions.

Documented image editing endpoint: `https://image-api.photoroom.com/v2/edit`; authentication uses `x-api-key`. Repeated calls can incur separate charges; cache product preparation per inventory item. Exact account pricing and terms were not established in this research. No paid Photoroom calls were made.

### Alibaba's Qwen team — Qwen-Image-Edit

Optional future self-hosted editing candidate.

Official model card: https://huggingface.co/Qwen/Qwen-Image-Edit-2511

The model card documents multi-image editing, consistency improvements and Apache 2.0 licensing. It requires GPU deployment or a hosting provider. Its published examples do not establish furniture-specific fidelity on our inventory. It is not integrated in Roomform.

### Meshy — optional image-to-3D service

Official API: https://docs.meshy.ai/en/api/image-to-3d

The documented API takes a product image and can produce textured GLB models and PBR maps. This could run automatically behind the scenes without seller modelling work. However, unseen surfaces are inferred. It is optional research, not the default recommended accuracy path. Commercial rights, account pricing and suitability require checking; no Meshy integration or paid test was completed.

### Microsoft — MoGe

Optional room-geometry assistance: https://github.com/microsoft/MoGe

The repository documents monocular depth, point maps, normals and camera information, with metric estimates in newer versions. These are placement priors, not guaranteed room measurements. Project/component/checkpoint licensing must be checked for the selected deployment. MoGe is not integrated in Roomform.

## Proposed automated chronology

1. Seller uploads one whole-product photograph and inventory facts. Optional additional angles improve coverage.
2. Automatically check focus, cropping and foreground segmentation; prepare and cache a cutout.
3. Buyer uploads a room photo and confirms budget, style and new/pre-loved preference.
4. Room/layout analysis selects suitable, available inventory and proposes positions consistent with room surfaces and a compatible product viewpoint.
5. Execute controlled product integration. Test BRIA as the specialized candidate, with FLUX and existing Gemini editing as separate benchmark candidates; do not assume all providers are needed for every image.
6. Automatically check product detail/silhouette/material agreement, room preservation, contact/occlusion, budget and inventory. Semantic similarity alone is insufficient to distinguish lookalike products. QA thresholds must be calibrated on evaluation data.
7. Deliver a passing result. If it fails, retry within a fixed spend/latency budget, use a more conservative compatible viewpoint, or return an actionable input request. No human approval is required, but automatic refusal of unsupported views must be allowed.
8. Persist product-to-region/SKU links so the buyer can tap the item, inspect original photos, see current price/stock and request purchase or consultation.
9. Single-item replacements must recheck inventory and budget and preserve the rest of the image as far as the edit boundaries allow.

## Current implementation versus proposed additions

Implemented in `/workspace/REA`:
- Real seller-photo upload, multiple angles, background removal with locally installed U2NETP/ONNX, cutout review and inventory linkage.
- Original-photo galleries and current price/stock information.
- Gemini-first and optional OpenAI reference-image adapters.
- Clickable hotspots, manual region marking and optional AI grounding.
- Masked single-item editing with lossless preservation of pixels outside the confirmed rectangle and fresh budget/availability checks.
- Private saved projects, beta AI attempt limits and existing marketplace workflows.

Not established or completed:
- Live Gemini image quality: no provider key was present at the latest implementation check; image-provider tests used simulated responses.
- Guaranteed SKU fidelity or verified physical fit.
- BRIA, FLUX, Photoroom, Qwen, Meshy or MoGe production integration.
- Fully automatic, calibrated final-result acceptance/retry routing. Current seller cutout approval and customer region confirmation are user interactions, not a staff output-review queue; further automation should reduce unnecessary input steps.
- A staff-free architecture does not imply every input must produce a purchasable rendering.

Latest implementation verification: 34 PostgreSQL tests, production frontend build and browser photo-upload-to-hotspot flow passed. Local neural matting was exercised on a real test photograph. These results are not an empirical benchmark of external image-generation fidelity.

## Next concrete evaluation

Use identical room/product pairs to compare BRIA, FLUX and Gemini. Include sofas, chairs, rugs, lamps, artwork and decorative objects; plain/patterned upholstery; used-item wear; varied lighting; and partial occlusion. Measure product identity, scene preservation, placement quality, failure/abstention rate, latency and total cost including retries and QA. Set acceptance targets from these results. Keep vendor feature claims separate from our measured results. No provider signup, paid subscription, external message or paid model request is authorized merely by the existence of this document; follow the user's actual instructions and configured credentials when executing the next stage.
