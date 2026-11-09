import React, { useEffect, useState } from "react";
import { styles, slug, categoryOptions } from "../../vendor-taxonomy";
import LocationFields from "./LocationFields";
export default function ProductFields({ item = {} }) {
  return (
    <>
      <div className="vendor-fields">
        <label>
          Product title
          <input
            name="name"
            required
            minLength={2}
            maxLength={160}
            defaultValue={item.name}
            placeholder="Walnut dining table"
          />
        </label>
        <label>
          Item category
          <select name="category" defaultValue={item.category || "sofa"}>
            {item.category && (
              <option value={item.category}>
                {item.category.replaceAll("_", " ")}
              </option>
            )}
            {categoryOptions()}
          </select>
        </label>
        <label>
          Primary design style
          <select name="style" defaultValue={item.style || "modern"}>
            {styles.map((s) => (
              <option key={s} value={slug(s)}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Condition
          <select name="condition" defaultValue={item.condition || "new"}>
            <option value="new">New</option>
            <option value="like_new">Pre-loved · like new</option>
            <option value="good">Pre-loved · good</option>
            <option value="fair">Pre-loved · fair</option>
          </select>
        </label>
        <label>
          Selling price
          <input
            name="price"
            type="number"
            step=".01"
            min=".01"
            max="10000000"
            required
            defaultValue={item.price}
          />
        </label>
        <label>
          Currency
          <select
            name="currency"
            disabled={!!item.id}
            defaultValue={item.currency || "PKR"}
          >
            {["PKR", "USD", "GBP", "EUR"].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Units in stock
          <input
            name="stock"
            type="number"
            min="0"
            max="1000000"
            required
            defaultValue={item.stock ?? 0}
          />
        </label>
        <label>
          Standard delivery estimate · days
          <input
            name="delivery_days"
            type="number"
            min="0"
            max="365"
            required
            defaultValue={item.delivery_days ?? 3}
          />
        </label>
      </div>
      <h3>Dimensions</h3>
      <div className="vendor-fields three">
        {["width_cm", "depth_cm", "height_cm"].map((n) => (
          <label key={n}>
            {n.replace("_cm", "")} · cm
            <input
              name={n}
              type="number"
              min=".1"
              max="2000"
              step=".1"
              required
              defaultValue={item[n]}
            />
          </label>
        ))}
      </div>
      <h3>Warehouse & delivery coverage</h3>
      <LocationFields item={item} />
      <div className="vendor-fields">
        <label>
          Delivery area
          <input
            name="delivery_location"
            required
            maxLength={200}
            defaultValue={item.delivery_location}
            placeholder="Karachi, Sindh"
          />
        </label>
        <label>
          Service radius · km
          <input
            name="delivery_radius_km"
            type="number"
            min=".1"
            max="500"
            step=".1"
            defaultValue={item.delivery_radius_km ?? 50}
            required
          />
        </label>
      </div>
    </>
  );
}
