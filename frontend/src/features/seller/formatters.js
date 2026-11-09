export const amount = (value, currency) =>
  new Intl.NumberFormat("en", { style: "currency", currency }).format(value);
