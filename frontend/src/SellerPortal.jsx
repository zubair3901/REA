import React, { useState } from "react";
import {
  Package,
  ClipboardList,
  Plus,
  LogOut,
  ArrowUpRight,
  Store,
} from "lucide-react";
import ProductPhotoStudio from "./ProductPhotoStudio";
import SellerOrders from "./SellerOrders";
import { call } from "./features/seller/api";
import { payload } from "./features/seller/listingPayload";
import ProductFields from "./features/seller/ProductFields";
import ProductEditor from "./features/seller/ProductEditor";
import InventoryList from "./features/seller/InventoryList";
import SellerAuth from "./features/seller/SellerAuth";
import SellerDashboard from "./features/seller/SellerDashboard";
import "./vendor.css";
export default function SellerPortal({ onPublished = async () => {} }) {
  const [session, setSession] = useState(null),
    [token, setToken] = useState(""),
    [mode, setMode] = useState("login"),
    [manualKey, setManualKey] = useState(""),
    [tab, setTab] = useState("dashboard"),
    [rows, setRows] = useState([]),
    [query, setQuery] = useState(""),
    [status, setStatus] = useState("all"),
    [edit, setEdit] = useState(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [photos, setPhotos] = useState([]),
    [primary, setPrimary] = useState("");

  async function load(key = token) {
    setBusy(true);
    setMessage("");
    try {
      setRows(await call("/api/seller/listings", key));
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function authenticate(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    const f = new FormData(e.currentTarget);
    try {
      const body = { email: f.get("email"), password: f.get("password") };
      if (mode === "register")
        Object.assign(body, { name: f.get("name"), kind: f.get("kind") });
      const s = await call("/api/sellers/" + mode, "", "POST", body);
      setSession(s);
      setToken(s.access_token);
      await load(s.access_token);
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    setBusy(true);
    try {
      if (session) await call("/api/sellers/logout", token, "POST");
      setToken("");
      setSession(null);
      setRows([]);
      setEdit(null);
      setPhotos([]);
      setPrimary("");
      setMessage("");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function publish(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    const form = e.currentTarget;
    try {
      if (!photos.length || photos.some((p) => !p.approved) || !primary)
        throw Error(
          "Prepare and approve your photographs, then choose a primary image.",
        );
      const body = payload(form);
      body.seller_id =
        session?.seller_id || new FormData(form).get("seller_id");
      Object.assign(body, {
        photo_ids: photos.map((p) => p.id),
        image_url: photos.find((p) => p.id === primary).cutout_url,
      });
      const a = await call("/api/assets", token, "POST", body);
      await load();
      await onPublished();
      setPhotos([]);
      setPrimary("");
      setEdit(a);
      setTab("inventory");
      setMessage(
        "Product published. Add catalog attributes and preparation/transit ranges in the edit panel.",
      );
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  const pending = session?.status === "pending";
  return (
    <div className="vendor-app">
      <header className="vendor-topbar">
        <a href="/" className="vendor-brand">
          <Store size={24} />
          roomform<span>Seller workspace</span>
        </a>
        <div>
          <a href="/" className="vendor-back">
            View marketplace <ArrowUpRight size={15} />
          </a>
          {token && (
            <button
              onClick={logout}
              disabled={busy}
              aria-label="Sign out seller"
            >
              <LogOut size={17} /> Sign out
            </button>
          )}
        </div>
      </header>
      {!token ? (
        <SellerAuth
          mode={mode}
          setMode={setMode}
          busy={busy}
          authenticate={authenticate}
          manualKey={manualKey}
          setManualKey={setManualKey}
          setToken={setToken}
          load={load}
        />
      ) : (
        <div className="vendor-layout">
          <aside className="vendor-sidebar">
            <p>Your workspace</p>
            {[
              ["dashboard", Package, "Dashboard"],
              ["inventory", ClipboardList, "My inventory"],
              ["new", Plus, "Add product"],
              ["orders", ClipboardList, "Delivery orders"],
            ].map(([id, Icon, title]) => (
              <button
                key={id}
                aria-current={tab === id ? "page" : undefined}
                onClick={() => {
                  setTab(id);
                  setEdit(null);
                  setMessage("");
                }}
              >
                <Icon size={19} />
                {title}
                {id === "inventory" && <span>{rows.length}</span>}
              </button>
            ))}
            <small>
              Roomform manages buyer agreements and project payments. Fulfil
              only the confirmed item, destination and delivery date supplied by
              the team.
            </small>
          </aside>
          <main className="vendor-main">
            <div className="vendor-page-title">
              <div>
                <h1>
                  {tab === "dashboard"
                    ? "Your inventory at a glance"
                    : tab === "inventory"
                      ? "My inventory"
                      : tab === "new"
                        ? "Add a product"
                        : "Delivery orders"}
                </h1>
                <p>
                  {pending
                    ? "Account pending review. Publishing becomes available after approval."
                    : "Manage your real products and keep the details up to date."}
                </p>
              </div>
              {tab !== "new" && (
                <button
                  className="rf-primary"
                  onClick={() => {
                    setTab("new");
                    setEdit(null);
                  }}
                >
                  <Plus size={17} /> Add product
                </button>
              )}
            </div>
            {message && (
              <p className="vendor-notice" role="status">
                {message}
              </p>
            )}
            {tab === "dashboard" && (
              <SellerDashboard rows={rows} setTab={setTab} />
            )}
            {tab === "new" && (
              <section className="vendor-product-form">
                <h2>Start with your photographs</h2>
                <p>
                  Upload the actual item. Review the prepared cutouts before
                  publishing.
                </p>
                <ProductPhotoStudio
                  token={token}
                  pending={pending}
                  photos={photos}
                  onChange={setPhotos}
                  primaryId={primary}
                  onPrimary={setPrimary}
                />
                <form className="merchant-form" onSubmit={publish}>
                  <fieldset disabled={pending || busy}>
                    {!session && (
                      <label>
                        Seller ID
                        <input name="seller_id" required maxLength={36} />
                      </label>
                    )}
                    <h2>Product details</h2>
                    <ProductFields />
                    <button className="rf-primary" disabled={busy || pending}>
                      {busy
                        ? "Publishing…"
                        : pending
                          ? "Approval required to publish"
                          : "Publish product"}
                    </button>
                  </fieldset>
                </form>
              </section>
            )}
            {tab === "inventory" && (
              <InventoryList
                rows={rows}
                query={query}
                setQuery={setQuery}
                status={status}
                setStatus={setStatus}
                load={load}
                busy={busy}
                setEdit={setEdit}
              />
            )}
            {tab === "orders" && <SellerOrders token={token} />}
          </main>
        </div>
      )}
      {edit && (
        <ProductEditor
          item={edit}
          token={token}
          listings={rows}
          onClose={() => setEdit(null)}
          onUpdate={async () => {
            await load();
            await onPublished();
          }}
        />
      )}
    </div>
  );
}
