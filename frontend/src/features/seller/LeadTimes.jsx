import React, { useEffect, useState } from "react";
import { call } from "./api";
export default function LeadTimes({ item, token }) {
  const [v, setV] = useState({}),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const keys = {
    ready_min_days: "Preparation · minimum days",
    ready_max_days: "Preparation · maximum days",
    delivery_min_days: "Transit · minimum days",
    delivery_max_days: "Transit · maximum days",
  };
  useEffect(() => {
    call("/api/assets/" + item.id + "/fulfillment", token)
      .then(setV)
      .catch((e) => setMessage(e.message));
  }, [item.id, token]);
  async function save() {
    setBusy(true);
    setMessage("");
    try {
      if (Object.keys(keys).some((k) => v[k] === undefined || v[k] === ""))
        throw Error("Enter all four lead-time values.");
      await call(
        "/api/assets/" + item.id + "/fulfillment",
        token,
        "PUT",
        Object.fromEntries(Object.keys(keys).map((k) => [k, Number(v[k])])),
      );
      setMessage("Lead times saved.");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="vendor-editor-section">
      <h3>Preparation & transit range</h3>
      <p>
        Roomform uses these ranges when scheduling a complete project. Your
        confirmed delivery instruction will specify the date and destination.
      </p>
      <div className="vendor-fields">
        {Object.entries(keys).map(([k, label]) => (
          <label key={k}>
            {label}
            <input
              type="number"
              min="0"
              max="365"
              required
              value={v[k] ?? ""}
              onChange={(e) => setV({ ...v, [k]: e.target.value })}
            />
          </label>
        ))}
      </div>
      <button
        type="button"
        className="rf-text-button"
        disabled={busy}
        onClick={save}
      >
        Save lead times
      </button>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
