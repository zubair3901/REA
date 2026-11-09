export function payload(form) {
  const f = new FormData(form),
    body = {};
  [
    "name",
    "category",
    "style",
    "currency",
    "condition",
    "delivery_location",
  ].forEach((k) => (body[k] = f.get(k)));
  [
    "price",
    "stock",
    "delivery_days",
    "width_cm",
    "depth_cm",
    "height_cm",
    "latitude",
    "longitude",
    "delivery_radius_km",
  ].forEach((k) => (body[k] = Number(f.get(k))));
  return body;
}
