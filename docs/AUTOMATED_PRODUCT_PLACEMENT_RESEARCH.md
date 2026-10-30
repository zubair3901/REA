# Automated product placement research — 2026-10-27

## Decision

Research official provider documentation for a service with no staff review queue and a one-photo minimum for sellers. Best initial commercial experiment: existing local cutout preparation + Gemini room/layout planning + BRIA Product Integration. Benchmark FLUX 3 Image as a separate reference-based editing candidate. These are recommendations based on documentation, not measured furniture-fidelity results or integrations already installed in Roomform.

## Closest fit: BRIA

Source: https://docs.bria.ai/product-shot-editing/products/product-integrate.md

The product integration endpoint accepts a scene image and one or more product images with x/y/width/height coordinates. Documentation states that it matches lighting, perspective and scene aesthetics. It supports a product photo without alpha with automatic cutout, but recommends its dedicated cutout endpoint first. Coordinates apply to the tightly cropped product, and the requested aspect ratio should match the product cutout to prevent stretching. Native blending/shadowing is described in best practices.

Source: https://docs.bria.ai/product-shots-best-practices.md

The provider specifically documents using a vision model for automatic surface/plane placement and batch QA. This fits an automated service, but does not establish SKU identity accuracy, true room measurements, or a guarantee of furniture realism on our inputs. The background-generation mode that explicitly preserves product pixels should not be conflated with a guarantee that every product-integration edit is pixel-identical.

## Alternative image editor: BFL

Sources:
- https://docs.bfl.ml/flux_3/flux3_image_layout.md
- https://docs.bfl.ml/guides/prompting_editing_multi_reference.md
- https://docs.bfl.ml/flux_2/flux2_image_editing.md

Current retrieved FLUX 3 documentation describes up to ten reference images, source/target bounding-box rows and anchor rows for preserving scene elements. Its multi-reference guide explicitly includes placing a lamp into a room. FLUX.2 documentation explicitly describes combining furniture from different photographs; its page distinguishes eight API reference images from ten in the playground. Hosted API and open-weight licenses must be evaluated separately. Neither editing capability alone proves exact product fidelity.

## Automatic product preparation: Photoroom

Sources:
- https://docs.photoroom.com/image-editing-api-plus-plan/ai-relight.md
- https://docs.photoroom.com/image-editing-api-plus-plan/uncertainty-score.md
- https://docs.photoroom.com/image-editing-api-plus-plan/pricing.md

Documented relighting includes ai.preserve-hue-and-saturation, intended to keep product colors close to the original. Cutout uncertainty is returned in x-uncertainty-score, ranging from zero (confident) to one (uncertain); -1 can indicate unavailable confidence. The documentation warns the score is not stable across model updates. It measures cutout uncertainty, not final product identity or physical fit. Pricing is per call, and repeated identical calls are billed separately according to the retrieved documentation; cache prepared inventory references in our application. Exact account pricing was not established here. Photoroom image-guided backgrounds can change the scene and should not be presented as guaranteed preservation of the buyer's room.

## Self-hosted candidate: Qwen-Image-Edit-2511

Source: https://huggingface.co/Qwen/Qwen-Image-Edit-2511

The official model card documents multi-image editing, improvements in consistency, geometry and viewpoint generation, and Apache 2.0 licensing. This is a GPU deployment/tuning alternative, not an already integrated service or proof of exact SKU fidelity. Official consistency examples are not a furniture-specific accuracy benchmark. Generated viewpoints infer unobserved surfaces.

## Optional hidden 3D processing: Meshy Image to 3D

Source: https://docs.meshy.ai/en/api/image-to-3d

Documented single-image input can produce textured models, GLB outputs and PBR maps. Sellers need not model anything themselves. However, unseen geometry/materials are inferred. This should be optional for viewpoint flexibility, not the default accuracy mechanism for a marketplace. No commercial-rights conclusion was drawn from a terms page that could not be retrieved. Merchant/API account terms and actual pricing require verification before adoption.

## Room geometry assistance

Source: https://github.com/microsoft/MoGe

MoGe documents monocular point maps, depth, normals and camera information; newer versions include metric estimates. These are useful automatic placement priors, not a substitute for measuring a room. Repository licensing distinguishes MIT project code from Apache-licensed DINOv2 components. Model/checkpoint terms still require checking for the selected deployment.

## Proposed fully automatic workflow

1. Seller uploads one clear, whole-product photograph and inventory information. Additional angles and a short clip are optional. Width/height/depth remain important for genuine fit claims; visual scale estimates alone are insufficient.
2. Prepare and cache a cutout; detect blur, cropping, occlusion and uncertain segmentation. Request a better photo only when the input fails the automated gate.
3. Analyze the buyer's room, propose affordable/available SKUs, and infer candidate floor/surface regions and a compatible viewing angle.
4. Render a bounded number of candidates using product-conditioned integration. Separate room finish edits from the product-preserving path.
5. Automatically score segmentation, instance similarity, silhouette, visible details, color/material agreement, scene preservation, floor contact, occlusion and inventory/budget validity. Semantic similarity alone cannot distinguish lookalike sofas; model confidence is not proof.
6. Deliver the highest passing result. On failure, retry within a strict cost cap, select a viewpoint compatible with the original photograph, or return an actionable request for better input. No human approval is required, but the service must be allowed to decline an unsupported rendering rather than invent a convincing false product.
7. Store SKU references and region maps for shopping hotspots, pricing and single-item replacement.

## Scope and evidence boundary

No paid provider calls, API-account signup, merchant commitment, production integration or empirical accuracy percentage resulted from this research. Documentation capabilities were checked online; they need a controlled comparison using our real furniture photographs and room images. Automated QA thresholds require validation on labeled evaluation data before customer-facing fidelity claims. A one-photo capture cannot reveal unknown product surfaces; use a compatible viewpoint or label reconstructed views as estimates.
