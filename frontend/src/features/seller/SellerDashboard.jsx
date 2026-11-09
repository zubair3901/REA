import React, { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
export default function SellerDashboard({ rows, setTab }) {
  return (
    <>
      <div className="vendor-stats">
        {[
          ["Listings", rows.length],
          ["Active products", rows.filter((a) => a.active).length],
          ["Units in stock", rows.reduce((sum, a) => sum + a.stock, 0)],
          ["Out of stock", rows.filter((a) => a.stock === 0).length],
        ].map(([label, value]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
      <section className="vendor-dashboard-summary">
        <h2>Keep your catalog ready</h2>
        <p>
          Use My inventory to update an individual product, change photos or set
          preparation and transit ranges. Your listings stay connected to
          customer project selections.
        </p>
        <button className="rf-text-button" onClick={() => setTab("inventory")}>
          Open inventory <ArrowUpRight size={17} />
        </button>
      </section>
    </>
  );
}
