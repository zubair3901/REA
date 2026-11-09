import React, { useEffect, useState } from "react";
import { call } from "./api";
import { styles, slug } from "../../vendor-taxonomy";
export default function Metadata({ item, token, listings }) {
  const [v, setV] = useState(null),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    call("/api/assets/" + item.id + "/catalog-details", token)
      .then((data) => setV(data.details))
      .catch((e) => setMessage(e.message));
  }, [item.id, token]);
  if (!v) return <p role="status">{message || "Loading catalog details…"}</p>;
  const textFields = {
    brand: "Brand / manufacturer",
    sku: "Merchant SKU",
    mpn: "Manufacturer part number",
    description: "Product description",
    materials: "Primary materials",
    finishes: "Finishes",
    textures: "Pattern / texture",
    silhouette: "Shape / silhouette",
  };
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const body = { ...v };
      if (
        body.shipping_dimensions_cm &&
        Object.values(body.shipping_dimensions_cm).every(
          (value) => value === null || value === "",
        )
      )
        body.shipping_dimensions_cm = null;
      await call(
        "/api/assets/" + item.id + "/catalog-details",
        token,
        "PUT",
        body,
      );
      setMessage("Catalog details saved.");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="vendor-editor-section" onSubmit={save}>
      <h3>Catalog details & matching attributes</h3>
      <p>
        Describe the actual product. These details help Roomform find suitable
        pieces; no generated furniture replaces your photographs.
      </p>
      <div className="vendor-fields">
        {Object.entries(textFields).map(([key, label]) => (
          <label key={key}>
            {label}
            {key === "description" ? (
              <textarea
                maxLength={4000}
                value={v[key] || ""}
                onChange={(e) => setV({ ...v, [key]: e.target.value })}
              />
            ) : (
              <input
                maxLength={key === "description" ? 4000 : 500}
                value={Array.isArray(v[key]) ? v[key].join(", ") : v[key] || ""}
                onChange={(e) =>
                  setV({
                    ...v,
                    [key]: ["materials", "finishes", "textures"].includes(key)
                      ? e.target.value
                          .split(",")
                          .map((s) => s.trim())
                          .filter(Boolean)
                      : e.target.value,
                  })
                }
              />
            )}
          </label>
        ))}
        <label>
          Parent product / variant
          <select
            value={v.parent_asset_id || ""}
            onChange={(e) =>
              setV({ ...v, parent_asset_id: e.target.value || null })
            }
          >
            <option value="">Standalone product</option>
            {listings
              .filter((a) => a.id !== item.id)
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
          </select>
        </label>
        <label>
          Placement
          <select
            value={v.placement || "freestanding"}
            onChange={(e) => setV({ ...v, placement: e.target.value })}
          >
            {[
              "freestanding",
              "floor-standing",
              "wall-mounted",
              "tabletop-only",
            ].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Product weight · kg
          <input
            type="number"
            min="0"
            step=".01"
            value={v.weight_kg ?? ""}
            onChange={(e) =>
              setV({
                ...v,
                weight_kg:
                  e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </label>
        <label>
          Shipping weight · kg
          <input
            type="number"
            min="0"
            step=".01"
            value={v.shipping_weight_kg ?? ""}
            onChange={(e) =>
              setV({
                ...v,
                shipping_weight_kg:
                  e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </label>
      </div>
      <h4>Shipping & reference prices</h4>
      <div className="vendor-fields">
        {["width", "depth", "height"].map((key) => (
          <label key={key}>
            Shipping {key} · cm
            <input
              type="number"
              min="0.1"
              max="3000"
              step=".1"
              value={v.shipping_dimensions_cm?.[key] ?? ""}
              onChange={(e) =>
                setV({
                  ...v,
                  shipping_dimensions_cm: {
                    ...v.shipping_dimensions_cm,
                    [key]:
                      e.target.value === "" ? null : Number(e.target.value),
                  },
                })
              }
            />
          </label>
        ))}
        {[
          ["msrp", "Retail reference price"],
          ["sale_price", "Promotional reference price"],
        ].map(([key, label]) => (
          <label key={key}>
            {label}
            <input
              type="number"
              min="0.01"
              max="10000000"
              step=".01"
              value={v[key] ?? ""}
              onChange={(e) =>
                setV({
                  ...v,
                  [key]: e.target.value === "" ? null : Number(e.target.value),
                })
              }
            />
          </label>
        ))}
      </div>
      <p>
        Reference prices do not change the selling price. Update the product
        selling price above to change the amount used in project estimates.
        Enter all three shipping dimensions together, or leave them blank.
      </p>
      <fieldset className="vendor-style-tags">
        <legend>Design style tags</legend>
        {styles.map((s) => (
          <label key={s}>
            <input
              type="checkbox"
              checked={(v.style_tags || []).includes(slug(s))}
              onChange={(e) =>
                setV({
                  ...v,
                  style_tags: e.target.checked
                    ? [...(v.style_tags || []), slug(s)]
                    : (v.style_tags || []).filter((t) => t !== slug(s)),
                })
              }
            />
            {s}
          </label>
        ))}
      </fieldset>
      <label>
        Dominant color name
        <input
          value={v.dominant_colors?.[0]?.name || ""}
          onChange={(e) =>
            setV({
              ...v,
              dominant_colors: [
                {
                  name: e.target.value,
                  hex: v.dominant_colors?.[0]?.hex || "#808080",
                },
              ],
            })
          }
        />
      </label>
      <label>
        Dominant color hex
        <input
          type="color"
          value={v.dominant_colors?.[0]?.hex || "#808080"}
          onChange={(e) =>
            setV({
              ...v,
              dominant_colors: [
                {
                  name: v.dominant_colors?.[0]?.name || "Primary color",
                  hex: e.target.value,
                },
              ],
            })
          }
        />
      </label>
      <button className="rf-primary" disabled={busy}>
        {busy ? "Saving…" : "Save catalog details"}
      </button>
      {message && <p role="status">{message}</p>}
    </form>
  );
}
