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
export function Consultation({ projectId, professionalId, onDone }) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api("/api/workspace/services", "POST", {
        ...f,
        project_id: projectId,
        professional_id: professionalId || null,
        consent: true,
      });
      onDone?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="ws-card ws-form" onSubmit={submit}>
      <h2>
        {professionalId
          ? "Find the right hands for your home."
          : "Lock in your direction. Meet your designer."}
      </h2>
      <p>
        Your project budget, location, and brief help the team prepare. This
        sends a request; a time and any consultation fee will be confirmed
        separately.
      </p>
      <label>
        What would you like help with?
        <textarea
          name="brief"
          required
          minLength={10}
          maxLength={2000}
          placeholder="Tell us about the space, your priorities and your timeline…"
        />
      </label>
      <div className="form-row">
        <label>
          Phone / WhatsApp
          <input
            name="phone"
            type="tel"
            required
            minLength={6}
            maxLength={40}
          />
        </label>
        <label>
          Preferred date · optional
          <input
            name="preferred_date"
            type="date"
            min={new Date().toISOString().slice(0, 10)}
          />
        </label>
      </div>
      <label className="consent">
        <input type="checkbox" required /> Share my request and contact details
        with the assigned professional or consultation team.
      </label>
      <button className="rf-primary" disabled={busy || !projectId}>
        {busy ? "Sending…" : "Request a conversation"}{" "}
        <ArrowUpRight size={16} />
      </button>
      <Notice error>{error}</Notice>
    </form>
  );
}
