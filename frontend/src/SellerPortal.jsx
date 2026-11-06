import React, { useEffect, useState } from "react";
import SellerOrders from "./SellerOrders";
import ProductPhotoStudio from "./ProductPhotoStudio";
import "./finalization.css";

import {
  ArrowRight,
  Check,
  LoaderCircle,
  Plus,
  RefreshCw,
  ShoppingBag,
  LogOut,
} from "lucide-react";
const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const media = (p) => (p?.startsWith("/") ? API + p : p);
const conditionLabels = {
  new: "New",
  like_new: "Pre-owned · like new",
  good: "Pre-owned · good",
  fair: "Pre-owned · fair",
};
async function call(path, options = {}) {
  const r = await fetch(API + path, options);
  let data;
  try {
    data = await r.json();
  } catch {
    throw Error("Unexpected server response. Please try again.");
  }
  if (!r.ok)
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail || "Request failed"),
    );
  return data;
}
function Fulfillment({ item, token }) {
  const [values, setValues] = useState(null), [message, setMessage] = useState(""), [busy, setBusy] = useState(false);
  const fields = {ready_min_days:"Ready in · minimum days",ready_max_days:"Ready in · maximum days",delivery_min_days:"Delivery · minimum days",delivery_max_days:"Delivery · maximum days"};
  useEffect(() => { let live=true; call("/api/assets/"+item.id+"/fulfillment", {headers:{"X-Merchant-Key":token}}).then(data=>{if(live)setValues(data)}).catch(()=>{if(live)setValues({})});return()=>{live=false}; }, [item.id,token]);
  async function save() {
    setBusy(true);setMessage("");
    try { const body=Object.fromEntries(Object.keys(fields).map(key=>[key,Number(values[key])]));
      if(Object.keys(fields).some(key=>values[key]===undefined||values[key]===""))throw Error("Enter all four lead times.");
      if(body.ready_min_days>body.ready_max_days||body.delivery_min_days>body.delivery_max_days)throw Error("Minimum days cannot exceed maximum days.");
      await call("/api/assets/"+item.id+"/fulfillment",{method:"PUT",headers:{"Content-Type":"application/json","X-Merchant-Key":token},body:JSON.stringify(body)});setMessage("Lead times saved.");
    } catch(e) {setMessage(e.message)} finally {setBusy(false)}
  }
  return <section className="seller-fulfillment"><h4>Preparation & delivery range</h4><p>Set the days needed to make this item ready, followed by transit to the customer. Finalization estimates use both ranges.</p>{values ? <><div>{Object.entries(fields).map(([key,label])=><label key={key}>{label}<input aria-label={label} type="number" min="0" max="365" step="1" value={values[key]??""} onChange={e=>setValues({...values,[key]:e.target.value})}/></label>)}</div><button type="button" className="rf-text-button" disabled={busy} onClick={save}>{busy?"Saving lead times…":"Save lead times"}</button></>:<p>Loading lead times…</p>}{message&&<p role="status">{message}</p>}</section>;
}
function Listing({ item, token, onUpdate }) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    const f = new FormData(e.currentTarget);
    try {
      await call("/api/assets/" + encodeURIComponent(item.id), {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Merchant-Key": token,
        },
        body: JSON.stringify({
          price: Number(f.get("price")),
          stock: Number(f.get("stock")),
          delivery_days: Number(f.get("delivery_days")),
          active: f.get("active") === "on",
        }),
      });
      setMessage("Listing updated.");
      await onUpdate();
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="seller-listing" onSubmit={save}>
      <div className="listing-identity">
        <img src={media(item.image_url)} alt={item.name} />
        <div>
          <strong>{item.name}</strong>
          <span>
            {conditionLabels[item.condition] || "New"} · {item.currency}
          </span>
          <small>
            {item.active ? "Active listing" : "Hidden listing"} · {item.stock}{" "}
            in stock
          </small>
        </div>
      </div>
      <div className="form-row three">
        <label>
          Price · {item.currency}
          <input
            name="price"
            type="number"
            min="0.01"
            max="10000000"
            step="0.01"
            required
            defaultValue={item.price}
          />
        </label>
        <label>
          Stock
          <input
            name="stock"
            type="number"
            min="0"
            max="1000000"
            step="1"
            required
            defaultValue={item.stock}
          />
        </label>
        <label>
          Delivery · days
          <input
            name="delivery_days"
            type="number"
            min="0"
            max="365"
            step="1"
            required
            defaultValue={item.delivery_days}
          />
        </label>
      </div>
      <Fulfillment item={item} token={token}/>
      <div className="listing-actions">
        <label className="consent">
          <input name="active" type="checkbox" defaultChecked={item.active} />{" "}
          Show listing in catalog
        </label>
        <button className="button light" disabled={busy}>
          {busy ? (
            <LoaderCircle className="spin" size={15} />
          ) : (
            <Check size={15} />
          )}
          Save changes
        </button>
      </div>
      {message && (
        <p className="seller-message" role="alert">
          {message}
        </p>
      )}
    </form>
  );
}
export default function SellerPortal({ onPublished }) {
  const [sellerTab, setSellerTab] = useState("new");
  const [photoAssetId, setPhotoAssetId] = useState("");
  const [photos, setPhotos] = useState([]),
    [primaryId, setPrimaryId] = useState("");
  const [mode, setMode] = useState("register"),
    [session, setSession] = useState(null),
    [token, setToken] = useState(""),
    [busy, setBusy] = useState(false),
    [publishing, setPublishing] = useState(false),
    [message, setMessage] = useState(""),
    [publishMessage, setPublishMessage] = useState(""),
    [listings, setListings] = useState([]),
    [listBusy, setListBusy] = useState(false),
    [listError, setListError] = useState("");
  useEffect(() => {
    setPhotos([]);
    setPrimaryId("");
  }, [token]);
  async function loadListings(key = token) {
    setListBusy(true);
    setListError("");
    try {
      setListings(
        await call("/api/seller/listings", {
          headers: { "X-Merchant-Key": key },
        }),
      );
    } catch (e) {
      setListError(e.message);
    } finally {
      setListBusy(false);
    }
  }
  async function authenticate(e) {
    e.preventDefault();
    const form = e.currentTarget;
    setBusy(true);
    setMessage("");
    try {
      const f = new FormData(form),
        body = { email: f.get("email"), password: f.get("password") };
      if (mode === "register") {
        body.name = f.get("name");
        body.kind = f.get("kind");
      }
      const data = await call(
        "/api/sellers/" + (mode === "register" ? "register" : "login"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      setSession(data);
      setToken(data.access_token);
      form.reset();
      await loadListings(data.access_token);
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function signOut() {
    if (session && token) {
      try {
        await call("/api/sellers/logout", {
          method: "POST",
          headers: { "X-Merchant-Key": token },
        });
      } catch (e) {
        setMessage("Could not end the server session. Please retry sign out.");
        return;
      }
    }
    setSession(null);
    setToken("");
    setListings([]);
    setPhotos([]);
    setPrimaryId("");
    setMessage("");
    setPublishMessage("");
    setListError("");
  }
  async function publish(e) {
    e.preventDefault();
    const form = e.currentTarget;
    setPublishing(true);
    setPublishMessage("");
    try {
      const f = new FormData(form);
      if (!photos.length || photos.some((p) => !p.approved))
        throw Error("Review and approve your product photos first.");
      const primary = photos.find((p) => p.id === primaryId);
      if (!primary) throw Error("Choose a primary photo.");
      const body = {
        image_url: primary.cutout_url,
        photo_ids: photos.map((p) => p.id),
      };
      [
        "seller_id",
        "name",
        "category",
        "style",
        "currency",
        "condition",
        "delivery_location",
      ].forEach((k) => (body[k] = f.get(k)));
      [
        "price",
        "width_cm",
        "height_cm",
        "depth_cm",
        "latitude",
        "longitude",
        "stock",
        "delivery_days",
        "delivery_radius_km",
      ].forEach((k) => (body[k] = Number(f.get(k))));
      await call("/api/assets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Merchant-Key": token,
        },
        body: JSON.stringify(body),
      });
      setPublishMessage(
        "Product published. Your listing is now available to room designers.",
      );
      form.reset();
      setPhotos([]);
      setPrimaryId("");
      await loadListings();
      await onPublished();
    } catch (e) {
      setPublishMessage(e.message);
    } finally {
      setPublishing(false);
    }
  }
  const pending = session?.status === "pending";
  return (
    <section className="partner-page">
      <div className="seller-intro">
        <div>
          <h1>
            Your furniture.
            <br />
            <em>Their perfect find.</em>
          </h1>
          <p>
            A local shop. An independent maker. A sofa ready for its next home.
            Turn real photographs into a storefront made for discovery.
          </p>
          <div className="seller-benefits">
            <span>
              <Check size={15} /> New & pre-loved welcome
            </span>
            <span>
              <Check size={15} /> Your price. Your stock.
            </span>
            <span>
              <Check size={15} /> Local delivery, clearly defined
            </span>
          </div>
        </div>
        <div className="seller-intro-image">
          <img
            src="/images/dining.jpg"
            alt="Thoughtfully furnished dining space with natural materials"
          />
          <span>
            Great pieces deserve
            <br />
            <em>to be seen.</em>
          </span>
        </div>
      </div>
      <section className="seller-account">
        <div className="panel-title">
          <h2>
            {session ? "Your seller account" : "Start selling with Roomform"}
          </h2>
          <ShoppingBag size={20} />
        </div>
        {session ? (
          <>
            <div className="seller-session">
              <div>
                <span className={"pill " + (pending ? "pending" : "")}>
                  {pending ? "PENDING REVIEW" : "APPROVED SELLER"}
                </span>
                <p>
                  Seller ID <code>{session.seller_id}</code>
                </p>
                <small>
                  {pending
                    ? "Your seller account is awaiting review. Publishing is unavailable until approval. Sign out and sign in again to check your approval status."
                    : "Your account can publish and manage its own products."}
                </small>
              </div>
              <button className="button signout" onClick={signOut}>
                <LogOut size={14} />
                Sign out
              </button>
            </div>
            {pending && (
              <button
                className="check-status"
                onClick={() => {
                  signOut();
                  setMode("login");
                }}
              >
                Sign in again to check approval status <ArrowRight size={14} />
              </button>
            )}
          </>
        ) : (
          <>
            <div className="account-tabs">
              <button
                className={mode === "register" ? "active" : ""}
                aria-pressed={mode === "register"}
                disabled={busy}
                onClick={() => {
                  setMode("register");
                  setMessage("");
                }}
              >
                Register as a seller
              </button>
              <button
                className={mode === "login" ? "active" : ""}
                aria-pressed={mode === "login"}
                disabled={busy}
                onClick={() => {
                  setMode("login");
                  setMessage("");
                }}
              >
                Sign in
              </button>
            </div>
            <form onSubmit={authenticate} aria-busy={busy}>
              {mode === "register" && (
                <div className="form-row">
                  <label>
                    Your name or shop name
                    <input
                      name="name"
                      required
                      minLength="2"
                      maxLength="160"
                      autoComplete="organization"
                      placeholder="Studio & Co."
                    />
                  </label>
                  <label>
                    Seller type
                    <select name="kind">
                      <option value="merchant">
                        Furniture or decor merchant
                      </option>
                      <option value="individual">
                        Individual / pre-owned seller
                      </option>
                    </select>
                  </label>
                </div>
              )}
              <div className="form-row">
                <label>
                  Email address
                  <input
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    maxLength="254"
                    placeholder="you@example.com"
                  />
                </label>
                <label>
                  Password
                  <input
                    name="password"
                    type="password"
                    required
                    minLength={mode === "register" ? 12 : 1}
                    maxLength="128"
                    autoComplete={
                      mode === "register" ? "new-password" : "current-password"
                    }
                    placeholder={
                      mode === "register"
                        ? "At least 12 characters"
                        : "Your password"
                    }
                  />
                </label>
              </div>
              <button className="button light" disabled={busy}>
                {busy ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <ArrowRight size={16} />
                )}{" "}
                {busy
                  ? mode === "register" ? "Creating account…" : "Signing in…"
                  : mode === "register"
                    ? "Create seller account"
                    : "Sign in to manage listings"}
              </button>
              {mode === "register" && (
                <small>
                  New accounts are reviewed before they can publish listings.
                  You’ll need to sign in again after closing this tab.
                </small>
              )}
            </form>
          </>
        )}
        {message && (
          <p className="seller-message" role="alert">
            {message}
          </p>
        )}
        <details className="manual-access">
          <summary>Use an existing merchant access key</summary>
          <label>
            Merchant key or seller access token
            <input
              type="password"
              value={token}
              onChange={(e) => {
                setToken(e.target.value);
                setSession(null);
                setListings([]);
              }}
              autoComplete="off"
              placeholder="Existing server-issued key"
            />
          </label>
          <button
            className="button key-connect"
            disabled={!token || listBusy}
            onClick={() => loadListings()}
          >
            Load my listings <ArrowRight size={14} />
          </button>
        </details>
      </section>
      {token && (
        <>
          <nav className="seller-workspace-tabs" aria-label="Seller workspace">
            {[
              ["new", "Create a listing"],
              ["inventory", "My inventory"],
              ["orders", "Orders & delivery"],
            ].map(([id, title]) => (
              <button
                key={id}
                aria-pressed={sellerTab === id}
                onClick={() => setSellerTab(id)}
              >
                {title}
                {id === "inventory" && <span>{listings.length}</span>}
              </button>
            ))}
          </nav>
          {sellerTab === "new" && (
            <>
              <div className="seller-flow-heading">
                <h2>
                  Photo first. Details next.
                  <br />
                  <em>Ready for a new home.</em>
                </h2>
                <p>
                  Start with one clear photo. More angles are optional. Review
                  the cutout, then add the details buyers need.
                </p>
              </div>
              <section className="photo-listing-mode">
                <label>
                  Photographs for
                  <select
                    value={photoAssetId}
                    onChange={(e) => {
                      setPhotoAssetId(e.target.value);
                      setPhotos([]);
                      setPrimaryId("");
                    }}
                  >
                    <option value="">A new listing</option>
                    {listings.map((a) => (
                      <option key={a.id} value={a.id}>
                        Update photos · {a.name}
                      </option>
                    ))}
                  </select>
                </label>
              </section>
              <ProductPhotoStudio
                token={token}
                pending={pending}
                photos={photos}
                onChange={setPhotos}
                primaryId={primaryId}
                onPrimary={setPrimaryId}
              />
              {photoAssetId && (
                <button
                  className="rf-primary"
                  disabled={
                    !photos.length ||
                    photos.some((p) => !p.approved) ||
                    !primaryId ||
                    publishing
                  }
                  onClick={async () => {
                    setPublishing(true);
                    setPublishMessage("");
                    try {
                      await call(
                        "/api/seller/listings/" + photoAssetId + "/photos",
                        {
                          method: "POST",
                          headers: {
                            "Content-Type": "application/json",
                            "X-Merchant-Key": token,
                          },
                          body: JSON.stringify({
                            photo_ids: photos.map((p) => p.id),
                            image_url: photos.find((p) => p.id === primaryId)
                              .cutout_url,
                          }),
                        },
                      );
                      setPhotos([]);
                      setPrimaryId("");
                      setPhotoAssetId("");
                      await loadListings();
                      await onPublished();
                      setPublishMessage("Listing photographs updated.");
                    } catch (e) {
                      setPublishMessage(e.message);
                    } finally {
                      setPublishing(false);
                    }
                  }}
                >
                  Save photographs to selected listing
                </button>
              )}
              <form className="merchant-form" onSubmit={publish}>
                <div className="panel-title">
                  <h2>Publish a product</h2>
                  <Plus size={20} />
                </div>
                {!token && (
                  <p className="seller-guidance">
                    Create an account or sign in above to publish a product.
                  </p>
                )}
                <fieldset
                  disabled={!token || pending || publishing || !!photoAssetId}
                >
                  <div className="form-row">
                    <label>
                      Seller ID
                      <input
                        name="seller_id"
                        key={session?.seller_id || "manual"}
                        defaultValue={session?.seller_id || ""}
                        readOnly={!!session}
                        required
                        maxLength="36"
                        placeholder="Your seller ID"
                      />
                    </label>
                    <label>
                      Item name
                      <input
                        name="name"
                        minLength="2"
                        maxLength="160"
                        required
                        placeholder="Arc lounge chair"
                      />
                    </label>
                  </div>
                  <div className="form-row">
                    <label>
                      Category
                      <select name="category">
                        <option value="chair">Chair</option>
                        <option value="sofa">Sofa</option>
                        <option value="lamp">Lamp</option>
                        <option value="table">Table</option>
                        <option value="decor">Decor</option>
                        <option value="bed">Bed</option>
                        <option value="desk">Desk</option>
                        <option value="rug">Rug</option>
                        <option value="storage">Storage</option>
                        <option value="art">Wall art</option>
                        <option value="textiles">Textiles</option>
                      </select>
                    </label>
                    <label>
                      Style
                      <select name="style">
                        <option value="minimalist">Minimalist</option>
                        <option value="modern">Modern</option>
                        <option value="mid-century">Mid-century</option>
                        <option value="scandinavian">Scandinavian</option>
                      </select>
                    </label>
                  </div>
                  <label>
                    Item condition
                    <select name="condition">
                      <option value="new">New</option>
                      <option value="like_new">Pre-owned · like new</option>
                      <option value="good">Pre-owned · good</option>
                      <option value="fair">Pre-owned · fair</option>
                    </select>
                  </label>
                  <div className="form-row">
                    <label>
                      Price
                      <input
                        name="price"
                        type="number"
                        min="0.01"
                        max="10000000"
                        step="0.01"
                        required
                      />
                    </label>
                    <label>
                      Currency
                      <select name="currency">
                        <option>USD</option>
                        <option>PKR</option>
                        <option>GBP</option>
                        <option>EUR</option>
                      </select>
                    </label>
                  </div>
                  <div className="form-row three">
                    {["width_cm", "height_cm", "depth_cm"].map((n) => (
                      <label key={n}>
                        {n.replace("_cm", "")} · cm
                        <input
                          type="number"
                          min="0.1"
                          max="2000"
                          step="0.1"
                          name={n}
                          required
                        />
                      </label>
                    ))}
                  </div>
                  <div className="form-row">
                    <label>
                      Latitude
                      <input
                        name="latitude"
                        type="number"
                        min="-90"
                        max="90"
                        step="any"
                        required
                      />
                    </label>
                    <label>
                      Longitude
                      <input
                        name="longitude"
                        type="number"
                        min="-180"
                        max="180"
                        step="any"
                        required
                      />
                    </label>
                  </div>
                  <div className="form-row">
                    <label>
                      Delivery location
                      <input
                        name="delivery_location"
                        required
                        maxLength="200"
                        placeholder="Karachi, Sindh"
                      />
                    </label>
                    <label>
                      Delivery radius · km
                      <input
                        name="delivery_radius_km"
                        type="number"
                        min="0.1"
                        max="500"
                        step="0.1"
                        defaultValue="50"
                        required
                      />
                    </label>
                  </div>
                  <div className="form-row">
                    <label>
                      Units in stock
                      <input
                        name="stock"
                        type="number"
                        min="0"
                        max="1000000"
                        step="1"
                        required
                      />
                    </label>
                    <label>
                      Delivery lead time · days
                      <input
                        name="delivery_days"
                        type="number"
                        min="0"
                        max="365"
                        step="1"
                        required
                      />
                    </label>
                  </div>
                  <p className="seller-guidance">
                    This listing uses your reviewed photos above. Show the
                    actual item and disclose wear accurately. No synthetic model
                    will replace your product.
                  </p>
                  <button
                    className="button light"
                    disabled={!token || pending || publishing || !!photoAssetId}
                  >
                    {publishing ? (
                      <LoaderCircle className="spin" size={18} />
                    ) : (
                      <Plus size={18} />
                    )}{" "}
                    {publishing
                      ? "Publishing…"
                      : pending
                        ? "Approval required to publish"
                        : "Publish product"}
                  </button>
                </fieldset>
                {publishMessage && (
                  <p className="seller-message" role="alert">
                    {publishMessage}
                  </p>
                )}
              </form>
            </>
          )}
          {sellerTab === "inventory" && (
            <section className="seller-inventory">
              <div className="panel-title">
                <h2>Your inventory</h2>
                <button
                  className="refresh-listings"
                  onClick={() => loadListings()}
                  disabled={!token || listBusy}
                >
                  <RefreshCw size={14} className={listBusy ? "spin" : ""} />
                  Refresh
                </button>
              </div>
              <p className="seller-guidance">
                Manage prices, stock, delivery times and visibility. Hidden
                listings remain available here.
              </p>
              {listError && (
                <p className="seller-message" role="alert">
                  {listError}
                </p>
              )}
              {!listings.length && !listBusy && (
                <p className="seller-empty">
                  {token
                    ? "No listings loaded. Refresh your inventory or publish your first piece."
                    : "Sign in to see your listings."}
                </p>
              )}
              {listings.map((item) => (
                <Listing
                  key={
                    item.id +
                    "-" +
                    JSON.stringify([
                      item.price,
                      item.stock,
                      item.active,
                      item.delivery_days,
                    ])
                  }
                  item={item}
                  token={token}
                  onUpdate={async () => {
                    await loadListings();
                    await onPublished();
                  }}
                />
              ))}
            </section>
          )}
          {sellerTab === "orders" && <SellerOrders token={token} />}
        </>
      )}
    </section>
  );
}
