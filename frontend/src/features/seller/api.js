const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
export const image = (p) => (p?.startsWith("/") ? API + p : p);
export async function call(path, token, method = "GET", body) {
  const r = await fetch(API + path, {
    method,
    headers: {
      ...(token ? { "X-Merchant-Key": token } : {}),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (r.status === 204) return;
  const d = await r.json();
  if (!r.ok)
    throw Error(
      typeof d.detail === "string"
        ? d.detail
        : Array.isArray(d.detail)
          ? d.detail.map((i) => i.msg).join(". ")
          : "Could not save. Check the details and try again.",
    );
  return d;
}
