export const pageNames = {
  discover: "Home",
  inspiration: "Inspiration",
  studio: "Design studio",
  marketplace: "Shop",
  professionals: "Professionals",
  partners: "For sellers",
  seller: "Seller workspace",
  projects: "My projects",
  teams: "For business",
  consult: "Consultation",
  operations: "Operations",
};
export function initialPage() {
  const q = new URLSearchParams(location.search);
  return q.has("reset")
    ? "projects"
    : Object.hasOwn(pageNames, q.get("page"))
      ? q.get("page")
      : "discover";
}
