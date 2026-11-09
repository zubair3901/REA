/** Shared JSON transport; feature modules own endpoint selection and payloads. */
export const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
export async function api(path, method = "GET", body, headers = {}) {
  const response = await fetch(API + path, {
    method,
    credentials: "include",
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(". ")
          : "Could not complete this request. Please try again.",
    );
  }
  return data;
}
