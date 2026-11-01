import React, { useEffect, useState } from "react";
import {
  Camera,
  Upload,
  Check,
  Trash2,
  LoaderCircle,
  Image as ImageIcon,
} from "lucide-react";
import { API, api } from "./workspace-api";
import "./photography.css";
export function OriginalPhoto({ photo, token, alt }) {
  const [src, setSrc] = useState("");
  useEffect(() => {
    let active = true,
      url = "";
    fetch(API + photo.original_url, {
      headers: token ? { "X-Merchant-Key": token } : {},
      credentials: "include",
    })
      .then((r) => {
        if (!r.ok) throw Error("Photo unavailable");
        return r.blob();
      })
      .then((blob) => {
        url = URL.createObjectURL(blob);
        if (active) setSrc(url);
        else URL.revokeObjectURL(url);
      })
      .catch(() => {});
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [photo.id, token]);
  return src ? (
    <img src={src} alt={alt || "Original seller photograph"} />
  ) : (
    <span className="photo-loading">Loading original photo…</span>
  );
}
export default function ProductPhotoStudio({
  token,
  pending,
  photos,
  onChange,
  primaryId,
  onPrimary,
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [progress, setProgress] = useState("");
  async function upload(files) {
    setError("");
    if (photos.length + files.length > 6) {
      setError("Use up to six angles for one product.");
      return;
    }
    setBusy(true);
    let prepared = [...photos];
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.size > 12 * 1024 * 1024)
          throw Error(file.name + " is larger than 12 MB.");
        setProgress(
          "Preparing " + file.name + " · background removal may take a moment",
        );
        const f = new FormData();
        f.append("file", file);
        f.append(
          "angle",
          ["front", "left", "right", "back", "detail", "angled"][
            prepared.length
          ],
        );
        const r = await fetch(API + "/api/seller/photos", {
          method: "POST",
          headers: { "X-Merchant-Key": token },
          body: f,
        });
        const d = await r.json();
        if (!r.ok)
          throw Error(
            typeof d.detail === "string"
              ? d.detail
              : "Could not prepare this photo",
          );
        prepared = [...prepared, d];
        onChange(prepared);
      }
      setProgress("Photos prepared. Review every cutout before publishing.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function approve(photo) {
    setError("");
    try {
      const d = await api(
        "/api/seller/photos/" + photo.id + "/approve",
        "POST",
        { approved: true, rights_confirmed: true },
        { "X-Merchant-Key": token },
      );
      onChange(photos.map((p) => (p.id === d.id ? d : p)));
      if (!primaryId) onPrimary(d.id);
    } catch (e) {
      setError(e.message);
    }
  }
  async function remove(photo) {
    setError("");
    try {
      await api("/api/seller/photos/" + photo.id, "DELETE", null, {
        "X-Merchant-Key": token,
      });
      onChange(photos.filter((p) => p.id !== photo.id));
      if (primaryId === photo.id) onPrimary("");
    } catch (e) {
      setError(e.message);
    }
  }
  return (
    <section className="photo-studio">
      <div className="photo-heading">
        <div>
          <span className="rf-kicker">YOUR ACTUAL PRODUCT. EVERY ANGLE.</span>
          <h2>
            No modelling.
            <br />
            <em>Just your photographs.</em>
          </h2>
          <p>
            Photograph the whole item in good daylight. One clear photo is
            enough to start. Additional angles are optional. We remove the
            background while keeping its photographed color, fabric, details and
            wear.
          </p>
        </div>
        <Camera size={32} />
      </div>
      <label className={"photo-drop " + (!token || pending ? "disabled" : "")}>
        <Upload size={25} />
        <strong>
          {busy ? "Preparing your photographs…" : "Upload product photos"}
        </strong>
        <span>JPG, PNG or WebP · up to six angles · 12 MB per photo</span>
        <input
          aria-label="Upload product photographs"
          type="file"
          multiple
          accept="image/jpeg,image/png,image/webp"
          disabled={!token || pending || busy || photos.length >= 6}
          onChange={(e) => {
            upload([...e.target.files]);
            e.target.value = "";
          }}
        />
      </label>
      {(!token || pending) && (
        <p className="photo-guidance">
          Sign in as an approved seller to prepare your product photographs.
          Secure staging also requires email verification.
        </p>
      )}
      <div className="photo-angle-guide">
        {["Front", "Left side", "Right side", "Back", "Close-up", "Angled"].map(
          (s, i) => (
            <span key={s}>
              <Camera size={13} />
              {i + 1}. {s}
            </span>
          ),
        )}
      </div>
      {progress && (
        <p className="ws-notice" role="status">
          {busy && <LoaderCircle size={14} className="spin" />} {progress}
        </p>
      )}
      {error && (
        <p className="ws-notice error" role="alert">
          {error}
        </p>
      )}
      <div className="photo-prepared-grid">
        {photos.map((photo) => (
          <PhotoReview
            key={photo.id}
            photo={photo}
            token={token}
            locked={busy}
            primary={primaryId === photo.id}
            onPrimary={() => onPrimary(photo.id)}
            onAngle={async (angle) => {
              const d = await api(
                "/api/seller/photos/" + photo.id,
                "PATCH",
                { angle },
                { "X-Merchant-Key": token },
              );
              onChange(photos.map((p) => (p.id === d.id ? d : p)));
            }}
            onApprove={() => approve(photo)}
            onRemove={() => remove(photo)}
          />
        ))}
      </div>
      {photos.length > 0 && (
        <p className="photo-guidance">
          Approve each cutout and choose the primary photo. Your approved
          original angles will be visible to buyers and can be sent to the
          selected AI provider when they request a room design.
        </p>
      )}
    </section>
  );
}
function PhotoReview({
  photo,
  token,
  locked,
  primary,
  onPrimary,
  onAngle,
  onApprove,
  onRemove,
}) {
  const [checked, setChecked] = useState(false),
    [working, setWorking] = useState(false),
    [error, setError] = useState("");
  async function run(fn) {
    setWorking(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    } finally {
      setWorking(false);
    }
  }
  return (
    <article className="photo-review">
      <div className="photo-review-top">
        <label>
          Photo angle
          <select
            aria-label="Photo angle"
            value={photo.angle}
            onChange={(e) => run(() => onAngle(e.target.value))}
            disabled={working || locked}
          >
            {["front", "left", "right", "back", "detail", "angled", "top"].map(
              (a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ),
            )}
          </select>
        </label>
        <button
          type="button"
          aria-label={"Remove " + photo.angle + " photo"}
          disabled={working || locked}
          onClick={() => run(onRemove)}
        >
          <Trash2 size={14} />
        </button>
      </div>
      <div className="photo-review-pair">
        <div>
          <OriginalPhoto photo={photo} token={token} />
          <small>Original</small>
        </div>
        <div>
          <img
            src={API + photo.cutout_url}
            alt={photo.angle + " product with background removed"}
          />
          <small>Prepared cutout</small>
        </div>
      </div>
      {photo.quality.warnings.map((w) => (
        <p className="photo-warning" key={w}>
          {w}
        </p>
      ))}
      {photo.approved ? (
        <p className="photo-approved">
          <Check size={14} /> Cutout approved
        </p>
      ) : (
        <>
          <label className="consent">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
            />{" "}
            The whole item is correctly cut out. I own these photos and agree to
            share them with buyers and design providers.
          </label>
          <button
            type="button"
            className="rf-primary"
            disabled={!checked || working || locked}
            onClick={() => run(onApprove)}
          >
            Approve this cutout
          </button>
        </>
      )}
      <label className="consent">
        <input
          type="radio"
          name="primary-product-photo"
          checked={primary}
          onChange={onPrimary}
          disabled={!photo.approved || locked}
        />{" "}
        Use as primary product photo
      </label>
      {error && <p role="alert">{error}</p>}
    </article>
  );
}
