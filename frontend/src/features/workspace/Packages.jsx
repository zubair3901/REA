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
export function Packages({ projectId }) {
  const [config, setConfig] = useState(null),
    [payments, setPayments] = useState([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const { user } = useWorkspace();
  async function load() {
    setConfig(await api("/api/workspace/packages"));
    if (user) setPayments(await api("/api/workspace/payments"));
  }
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [user]);
  async function run(fn) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="ws-toolbar">
        <div>
          <h2>A home project isn’t a monthly habit.</h2>
          <p>
            Pay once for your design package. Products, labor, delivery and
            consultation fees are separate.
          </p>
        </div>
      </div>
      <Notice>
        AI generation is being integrated later. Local product previews are
        free; image package sales are currently paused.
      </Notice>
      <div className="ws-pricing">
        {(config?.packages || []).map((p, i) => (
          <article key={p.id} className={"ws-price " + (i ? "featured" : "")}>
            <h3>{p.name}</h3>
            <strong>
              {money(p.amount)}
              <small> / project package</small>
            </strong>
            <p>{p.credits} AI image credits when available</p>
            <ul>
              <li>One saved project</li>
              <li>Budget and real-product planning</li>
              <li>Access to consultation requests</li>
            </ul>
            <button
              className="rf-primary"
              disabled={!projectId || busy || !config?.sales_enabled}
              onClick={() =>
                run(() =>
                  api(
                    "/api/workspace/projects/" + projectId + "/checkout",
                    "POST",
                    { package: p.id },
                  ),
                )
              }
            >
              {config?.sales_enabled
                ? "Choose package"
                : "Available when AI launches"}
            </button>
          </article>
        ))}
      </div>
      {config?.payment_instructions && (
        <p className="ws-notice" style={{ whiteSpace: "pre-wrap" }}>
          {config.payment_instructions}
        </p>
      )}
      {payments
        .filter((p) => p.project_id === projectId)
        .map((p) => (
          <form
            className="ws-card"
            key={p.id}
            onSubmit={(e) => {
              e.preventDefault();
              const reference = new FormData(e.currentTarget).get("reference");
              run(() =>
                api("/api/workspace/payments/" + p.id + "/reference", "POST", {
                  reference,
                }),
              );
            }}
          >
            <h3>
              {money(p.amount)} · {label(p.status)}
            </h3>
            <small>
              Payment #{p.id} · verified by the operations team before credits
              are added.
            </small>
            {["awaiting_payment", "submitted"].includes(p.status) && (
              <>
                <label>
                  Bank / provider transaction reference
                  <input
                    name="reference"
                    required
                    minLength={4}
                    maxLength={200}
                    defaultValue={p.reference}
                  />
                </label>
                <button className="rf-primary" disabled={busy}>
                  Submit payment reference
                </button>
                <button
                  type="button"
                  className="rf-text-button"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      const r = await api(
                        "/api/payments/" + p.id + "/card",
                        "POST",
                      );
                      window.location.assign(r.url);
                    })
                  }
                >
                  Pay by card / eligible Google Pay via hosted checkout
                </button>
              </>
            )}
          </form>
        ))}
      <Notice error>{error}</Notice>
    </>
  );
}
