import React, { useEffect, useState } from "react";
import { X } from "lucide-react";
import { call } from "./api";
import { payload } from "./listingPayload";
import ProductFields from "./ProductFields";
import Metadata from "./CatalogDetails";
import LeadTimes from "./LeadTimes";
import Photos from "./ProductPhotos";
export default function ProductEditor({
  item,
  token,
  listings,
  onClose,
  onUpdate,
}) {
  useEffect(() => {
    const previous = document.activeElement;
    const old = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const pane = document.querySelector(".vendor-editor");
    const focusable = () =>
      [
        ...pane.querySelectorAll(
          "button,input,select,textarea,a[href],summary",
        ),
      ].filter((el) => !el.disabled && el.getClientRects().length);
    focusable()[0]?.focus();
    const keydown = (e) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "Tab") {
        const controls = focusable();
        if (e.shiftKey && document.activeElement === controls[0]) {
          e.preventDefault();
          controls.at(-1)?.focus();
        } else if (!e.shiftKey && document.activeElement === controls.at(-1)) {
          e.preventDefault();
          controls[0]?.focus();
        }
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.body.style.overflow = old;
      previous?.focus();
    };
  }, [item.id]);
  return (
    <div className="vendor-editor-overlay">
      <section
        className="vendor-editor"
        role="dialog"
        aria-modal="true"
        aria-label={"Edit " + item.name}
      >
        <header>
          <div>
            <h2>Edit product</h2>
            <p>{item.name}</p>
            <small>Item code: {item.id}</small>
          </div>
          <button aria-label="Close product editor" onClick={() => onClose()}>
            <X size={22} />
          </button>
        </header>
        <EditCore item={item} token={token} onUpdate={onUpdate} />
        <Metadata item={item} token={token} listings={listings} />
        <LeadTimes item={item} token={token} />
        <Photos item={item} token={token} onUpdate={onUpdate} />
      </section>
    </div>
  );
}
function EditCore({ item, token, onUpdate }) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  return (
    <form
      className="vendor-editor-section"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setMessage("");
        try {
          const body = payload(e.currentTarget);
          delete body.currency;
          body.active = new FormData(e.currentTarget).get("active") === "on";
          await call("/api/assets/" + item.id, token, "PATCH", body);
          await onUpdate();
          setMessage("Product details saved.");
        } catch (e) {
          setMessage(e.message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <ProductFields item={item} />
      <label className="consent">
        <input name="active" type="checkbox" defaultChecked={item.active} />{" "}
        Show listing in catalog
      </label>
      <button className="rf-primary" disabled={busy}>
        {busy ? "Saving…" : "Save product details"}
      </button>
      {message && <p role="status">{message}</p>}
    </form>
  );
}
