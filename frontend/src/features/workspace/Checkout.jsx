import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Plus,
  FolderOpen,
  Users,
  Check,
  LogOut,
  ArrowRight,
  Wallet,
  Package,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { api, API, money, label } from "../../workspace-api";
import { useWorkspace } from "./WorkspaceContext";
import { Notice } from "./Notice";
export function Checkout({ assetIds, onDone }) {
  const { active, user } = useWorkspace();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [success, setSuccess] = useState("");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = new FormData(e.currentTarget);
    try {
      const result = await api("/api/workspace/orders", "POST", {
        project_id: active.id,
        items: assetIds.map((id) => ({
          asset_id: id,
          quantity: Number(f.get("qty_" + id) || 1),
        })),
        address: f.get("address"),
        phone: f.get("phone"),
        consent: true,
      });
      setSuccess(result.notice);
      onDone?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="ws-card ws-form" onSubmit={submit}>
      <h2>Request your selected pieces.</h2>
      <p>
        {active
          ? "For " + active.name
          : "Sign in and choose a saved project in My projects first."}{" "}
        · Roomform coordinates availability, delivery, taxes and payment with
        you. Sellers receive fulfillment instructions from our team. Demo
        illustrations cannot be purchased.
      </p>
      {assetIds.map((id) => (
        <label key={id}>
          Quantity · product {id.slice(0, 8)}
          <input
            name={"qty_" + id}
            type="number"
            min="1"
            max="100"
            defaultValue="1"
            required
          />
        </label>
      ))}
      <label>
        Delivery address
        <textarea
          name="address"
          required
          minLength={10}
          maxLength={500}
          placeholder="Street, neighborhood, city and postal code"
        />
      </label>
      <label>
        Contact phone
        <input type="tel" name="phone" required minLength={6} maxLength={40} />
      </label>
      <label className="consent">
        <input type="checkbox" required /> Share my project and delivery details
        with Roomform to coordinate fulfillment. Sellers receive only the
        necessary receiving instructions.
      </label>
      <button
        className="rf-primary"
        disabled={busy || !user || !active || !assetIds.length || !!success}
      >
        Send order request <ArrowRight size={16} />
      </button>
      <Notice error>{error}</Notice>
      <Notice>{success}</Notice>
    </form>
  );
}
