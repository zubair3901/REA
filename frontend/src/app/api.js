import { API } from "../workspace-api";
export { API };
export const media = (p) => (p?.startsWith("/") ? API + p : p);
export const money = (n, c = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: c }).format(
    Number(n || 0),
  );
export async function request(path, options) {
  const r = await fetch(API + path, { ...options, credentials: "include" });
  let d;
  try {
    d = await r.json();
  } catch {
    throw Error(
      "The service returned an unexpected response. Please try again.",
    );
  }
  if (!r.ok)
    throw Error(
      typeof d.detail === "string"
        ? d.detail
        : "Please check your details and try again.",
    );
  return d;
}
