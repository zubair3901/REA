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
import { Consultation } from "./Consultation";
import { Packages } from "./Packages";
import { EmailVerificationPanel } from "./EmailVerificationPanel";
import { SavedFinalizations } from "../../FinalizationBooking";
export default function Dashboard({ navigate, onDesign }) {
  const { user, projects, activeId, active, select, refresh, logout } =
    useWorkspace();
  const [detail, setDetail] = useState(null),
    [activity, setActivity] = useState({ orders: [], services: [] }),
    [create, setCreate] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [tab, setTab] = useState("designs"),
    [orgs, setOrgs] = useState([]);
  async function load() {
    if (!activeId) {
      setDetail(null);
      return;
    }
    const [d, a] = await Promise.all([
      api("/api/workspace/projects/" + activeId),
      api("/api/workspace/projects/" + activeId + "/activity"),
    ]);
    setDetail(d);
    setActivity(a);
  }
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [activeId]);
  useEffect(() => {
    api("/api/workspace/organizations")
      .then(setOrgs)
      .catch((e) => setError(e.message));
  }, []);
  async function run(fn) {
    setError("");
    setBusy(true);
    try {
      await fn();
      await refresh();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function newProject(e) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget));
    f.budget = Number(f.budget);
    f.organization_id = f.organization_id || null;
    await run(async () => {
      const p = await api("/api/workspace/projects", "POST", f);
      await refresh();
      select(p.id);
      setCreate(false);
    });
  }
  return (
    <>
      <div className="ws-heading">
        <div>
          <h1>
            Good to see you,
            <br />
            <em>{user.name.split(" ")[0]}.</em>
          </h1>
          <p>From your first idea to the final finishing touch.</p>
        </div>
        <button
          className="rf-text-button"
          onClick={() => run(logout)}
          disabled={busy}
        >
          <LogOut size={16} /> Sign out
        </button>
      </div>
      <EmailVerificationPanel />
      <div className="ws-stats">
        <article>
          <FolderOpen />
          <strong>{projects.length}</strong>
          <span>Saved projects</span>
        </article>
        <article>
          <Wallet />
          <strong>{projects.reduce((n, p) => n + p.credits, 0)}</strong>
          <span>Purchased image credits</span>
        </article>
        <article>
          <Users />
          <strong>{orgs.length}</strong>
          <span>Team workspaces</span>
        </article>
      </div>
      <div className="ws-toolbar">
        <h2>Your spaces</h2>
        <button className="rf-primary" onClick={() => setCreate(!create)}>
          <Plus size={16} /> New project
        </button>
      </div>
      <Notice error>{error}</Notice>
      {(create || !projects.length) && (
        <form className="ws-card ws-form" onSubmit={newProject}>
          <h3>Create a project</h3>
          <div className="form-row">
            <label>
              Project name
              <input
                name="name"
                required
                minLength={2}
                maxLength={160}
                placeholder="Our Karachi home"
              />
            </label>
            <label>
              City / neighborhood
              <input
                name="location"
                required
                minLength={2}
                maxLength={200}
                placeholder="Clifton, Karachi"
              />
            </label>
          </div>
          <div className="form-row three">
            <label>
              Total renovation budget
              <input
                name="budget"
                type="number"
                min="1"
                max="10000000"
                step="0.01"
                required
                placeholder="250000"
              />
            </label>
            <label>
              Currency
              <select name="currency">
                <option>PKR</option>
                <option>USD</option>
                <option>GBP</option>
                <option>EUR</option>
              </select>
            </label>
            <label>
              Products
              <select name="preference">
                <option value="either">New & pre-loved</option>
                <option value="new">New only</option>
                <option value="used">Pre-loved only</option>
              </select>
            </label>
          </div>
          <label>
            Workspace
            <select name="organization_id">
              <option value="">Personal project</option>
              {orgs
                .filter((o) => o.expires_at * 1000 > Date.now())
                .map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
            </select>
          </label>
          <button className="rf-primary" disabled={busy}>
            Create project <ArrowRight size={16} />
          </button>
        </form>
      )}
      <div className="ws-projects">
        {projects.map((p) => (
          <button
            key={p.id}
            className={"ws-project " + (activeId === p.id ? "selected" : "")}
            aria-pressed={activeId === p.id}
            onClick={() => {
              select(p.id);
              setTab("designs");
            }}
          >
            <span className="ws-project-icon">
              <FolderOpen size={24} />
            </span>
            <span className="ws-badge">{label(p.status)}</span>
            <h3>{p.name}</h3>
            <p>{p.location}</p>
            <strong>{money(p.budget, p.currency)}</strong>
            <small>
              {label(p.preference)} furniture · {p.credits} image credits
            </small>
          </button>
        ))}
      </div>
      {active && detail?.id === active.id && (
        <section className="ws-detail">
          <div className="ws-toolbar">
            <div>
              <h2>{active.name}</h2>
            </div>
            <label>
              Project stage
              <select
                value={active.status}
                disabled={busy}
                onChange={(e) =>
                  run(() =>
                    api("/api/workspace/projects/" + active.id, "PATCH", {
                      status: e.target.value,
                    }),
                  )
                }
              >
                {[
                  "planning",
                  "sourcing",
                  "in_progress",
                  "completed",
                  "archived",
                ].map((s) => (
                  <option key={s} value={s}>
                    {label(s)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="ws-tabs">
            {[
              ["designs", "Designs"],
              ["activity", "Orders & requests"],
              ["finalizations", "Finalization PDFs"],
              ["consultation", "Book a consultation"],
              ["package", "Project packages"],
            ].map(([id, title]) => (
              <button
                className={tab === id ? "active" : ""}
                aria-pressed={tab === id}
                key={id}
                onClick={() => setTab(id)}
              >
                {title}
              </button>
            ))}
          </div>
          {tab === "designs" && (
            <>
              <div className="ws-toolbar">
                <p>Your saved room previews appear here.</p>
                <button
                  className="rf-primary"
                  onClick={() => navigate("studio")}
                >
                  Open design studio <ArrowUpRight size={16} />
                </button>
              </div>
              {detail.designs.length ? (
                <div className="rf-project-grid">
                  {detail.designs.map((d) => (
                    <button key={d.id} onClick={() => onDesign(d)}>
                      <img
                        src={API + d.image_url}
                        alt={d.style + " room preview"}
                      />
                      <h3>{label(d.style)} concept</h3>
                      <span>
                        {money(d.quote.total, d.quote.currency)} estimated
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="ws-empty">
                  <FolderOpen size={32} />
                  <h3>No saved previews yet</h3>
                  <p>
                    Open the studio to create a room preview with local
                    products.
                  </p>
                </div>
              )}
            </>
          )}
          {tab === "activity" && (
            <>
              <div className="ws-toolbar">
                <h3>Orders and professional requests</h3>
                <button className="rf-text-button" onClick={() => run(load)}>
                  <RefreshCw size={16} /> Refresh
                </button>
              </div>
              {!activity.orders.length && !activity.services.length && (
                <div className="ws-empty">
                  <Package size={30} />
                  <h3>No requests yet</h3>
                  <p>Product orders and professional requests appear here.</p>
                  <button
                    className="rf-primary"
                    onClick={() => navigate("marketplace")}
                  >
                    Explore real products
                  </button>
                </div>
              )}
              {activity.orders.map((o) => (
                <article className="ws-card" key={o.id}>
                  <div className="ws-toolbar">
                    <h3>Order #{o.id.slice(0, 8)}</h3>
                    <span className="ws-badge">{label(o.status)}</span>
                  </div>
                  {o.items.map((i) => (
                    <p key={i.asset_id}>
                      {i.name} × {i.quantity}{" "}
                      <strong>{money(i.subtotal, o.currency)}</strong>
                    </p>
                  ))}
                  <p>
                    Items total: {money(o.total, o.currency)} · Shipping and
                    taxes agreed with seller.
                  </p>
                  <small>
                    {o.address} · No payment collected by this request.
                  </small>
                  {["requested", "confirmed"].includes(o.status) && (
                    <button
                      className="rf-text-button"
                      disabled={busy}
                      onClick={() =>
                        run(() =>
                          api(
                            "/api/workspace/orders/" + o.id + "/cancel",
                            "POST",
                          ),
                        )
                      }
                    >
                      Cancel order request
                    </button>
                  )}
                </article>
              ))}
              {activity.services.map((s) => (
                <article className="ws-card" key={s.id}>
                  <div className="ws-toolbar">
                    <h3>
                      {s.kind === "consultation"
                        ? "Design consultation"
                        : "Professional service"}
                    </h3>
                    <span className="ws-badge">{label(s.status)}</span>
                  </div>
                  <p>{s.brief}</p>
                  {s.preferred_date && (
                    <small>
                      Requested date: {s.preferred_date} · subject to
                      confirmation
                    </small>
                  )}
                  {s.response && <p className="ws-notice">{s.response}</p>}
                  {s.quoted_amount && (
                    <strong>
                      {money(s.quoted_amount, s.currency)} quoted · payment
                      agreed separately
                    </strong>
                  )}
                  <div className="ws-actions">
                    {(s.status === "quoted"
                      ? ["accepted", "declined"]
                      : ["requested", "accepted"].includes(s.status)
                        ? ["cancelled"]
                        : []
                    ).map((status) => (
                      <button
                        key={status}
                        disabled={busy}
                        className="rf-text-button"
                        onClick={() =>
                          run(() =>
                            api("/api/workspace/services/" + s.id, "PATCH", {
                              status,
                            }),
                          )
                        }
                      >
                        {status === "accepted"
                          ? "Accept quote"
                          : status === "declined"
                            ? "Decline quote"
                            : "Cancel request"}
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </>
          )}
          {tab === "finalizations" && (
            <SavedFinalizations projectId={activeId} />
          )}
          {tab === "consultation" && (
            <Consultation
              projectId={activeId}
              onDone={() => {
                setTab("activity");
                load();
              }}
            />
          )}
          {tab === "package" && <Packages projectId={activeId} />}
        </section>
      )}
    </>
  );
}
