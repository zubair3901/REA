import React, { useEffect, useState } from "react";
import { Search, RefreshCw, Package } from "lucide-react";
import { image } from "./api";
import { amount } from "./formatters";
export default function InventoryList({
  rows,
  query,
  setQuery,
  status,
  setStatus,
  load,
  busy,
  setEdit,
}) {
  const filtered = rows.filter(
    (r) =>
      (status === "all" ||
        (status === "active"
          ? r.active
          : status === "hidden"
            ? !r.active
            : r.stock === 0)) &&
      (!query ||
        (r.name + " " + r.id + " " + r.category)
          .toLowerCase()
          .includes(query.toLowerCase())),
  );
  return (
    <>
      <div className="vendor-inventory-toolbar">
        <label className="vendor-search">
          <Search size={18} />
          <input
            aria-label="Search inventory"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search product, category or item code"
          />
        </label>
        <select
          aria-label="Filter inventory"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="all">All listings</option>
          <option value="active">Active</option>
          <option value="hidden">Hidden</option>
          <option value="out">Out of stock</option>
        </select>
        <button
          className="rf-text-button"
          onClick={() => load()}
          disabled={busy}
        >
          <RefreshCw size={17} /> Refresh
        </button>
      </div>
      <div className="vendor-table-wrap">
        <table className="vendor-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Item code</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a) => (
              <tr key={a.id}>
                <td>
                  <div className="vendor-row-product">
                    <img src={image(a.image_url)} alt={a.name} loading="lazy" />
                    <div>
                      <strong>{a.name}</strong>
                      <small>
                        {a.category.replaceAll("_", " ")} ·{" "}
                        {a.condition.replaceAll("_", " ")}
                      </small>
                    </div>
                  </div>
                </td>
                <td>
                  <code>{a.id}</code>
                </td>
                <td>{amount(a.price, a.currency)}</td>
                <td>{a.stock}</td>
                <td>
                  <span
                    className={
                      "vendor-status " +
                      (!a.stock ? "empty" : a.active ? "active" : "")
                    }
                  >
                    {!a.stock ? "Out of stock" : a.active ? "Active" : "Hidden"}
                  </span>
                </td>
                <td>
                  <button className="rf-text-button" onClick={() => setEdit(a)}>
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!filtered.length && (
        <div className="vendor-empty">
          <Package size={30} />
          <h3>
            {rows.length ? "No matching products" : "Your catalog starts here"}
          </h3>
          <p>
            {rows.length
              ? "Try another search or filter."
              : "Add a product with real photographs, stock and delivery details."}
          </p>
        </div>
      )}
    </>
  );
}
