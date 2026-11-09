import React from "react";
import { ArrowRight, Check, MapPin } from "lucide-react";

import { Checkout } from "../Workspace";

export default function MarketplacePage({
  checkoutOpen,
  condition,
  filtered,
  findLocal,
  geoBusy,
  local,
  navigate,
  productGrid,
  search,
  selected,
  setCheckoutOpen,
  setCondition,
  setSearch,
}) {
  return (
    <main className="rf-section">
      <div className="rf-page-heading">
        <span className="rf-kicker">
          THOUGHTFULLY CHOSEN. READY FOR A NEW CHAPTER.
        </span>
        <h1>
          Find your next
          <br />
          <em>favorite piece.</em>
        </h1>
        <p>
          New finds and pre-loved character. Add up to eight pieces to your next
          room.
        </p>
      </div>
      <div className="rf-market-controls">
        <input
          aria-label="Search furniture"
          placeholder="Find a sofa, lamp, or something special…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label="Product condition"
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
        >
          <option value="all">All pieces</option>
          <option value="new">New</option>
          <option value="used">Pre-loved</option>
        </select>
        <button
          className="rf-text-button"
          onClick={findLocal}
          disabled={geoBusy}
        >
          <MapPin size={16} />
          {local ? "Show all locations" : "Near me · 50 km"}
        </button>
      </div>
      <p className="rf-subtle">
        Actual seller photography. Check every angle and confirm fit and
        delivery before ordering.
      </p>
      {productGrid(filtered)}
      {!filtered.length && (
        <p className="rf-empty-state">
          No pieces match just yet. Try another search or location.
        </p>
      )}
      <div className="rf-selection-bar">
        <span>{selected.length} pieces in your design</span>
        <button className="rf-primary" onClick={() => navigate("studio")}>
          Design with these pieces <ArrowRight size={17} />
        </button>
        <button
          className="rf-primary"
          onClick={() => setCheckoutOpen(!checkoutOpen)}
          disabled={!selected.length}
        >
          Request selected products
        </button>
      </div>
      {checkoutOpen && <Checkout assetIds={selected} />}
    </main>
  );
}
