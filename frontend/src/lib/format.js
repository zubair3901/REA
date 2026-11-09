/** Presentation helpers have no network or application-state dependencies. */
export const money = (value, currency = "USD") =>
  new Intl.NumberFormat("en", {
    style: "currency",
    currency,
  }).format(Number(value || 0));
export const label = (value) => value?.replaceAll("_", " ");
