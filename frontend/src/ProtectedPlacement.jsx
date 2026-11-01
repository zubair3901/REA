import React, { useEffect, useState } from "react";
import { Ruler, Undo2, ShieldCheck } from "lucide-react";
import "./protected-placement.css";
export const emptyPlacementSpec = () => ({
  floor_quad: [],
  floor_width_cm: 400,
  floor_depth_cm: 500,
  measurement_confirmed: false,
  placements: [],
  light_dx: 0.25,
  light_dy: 0.15,
});
export default function ProtectedPlacement({
  photo,
  assets,
  value,
  onChange,
  capabilities,
  cacheId,
}) {
  const [natural, setNatural] = useState({ width: 4, height: 3 }),
    [error, setError] = useState("");
  useEffect(() => {
    const existing = value.placements || [];
    const next = assets.map(
      (a, i) =>
        existing.find((p) => p.asset_id === a.id) || {
          asset_id: a.id,
          u: (i + 1) / (assets.length + 1),
          v: 0.8,
          view: a.category === "rug" ? "top" : "front",
        },
    );
    if (
      next.length !== existing.length ||
      next.some((p) => !existing.includes(p))
    )
      onChange({ ...value, placements: next });
  }, [assets.map((a) => a.id).join("|"),value.placements?.length]);
  function update(patch) {
    onChange({ ...value, ...patch });
  }
  function corner(e) {
    if (value.floor_quad.length >= 4) return;
    const r = e.currentTarget.getBoundingClientRect();
    update({
      floor_quad: [
        ...value.floor_quad,
        {
          x: Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)),
          y: Math.max(0, Math.min(1, (e.clientY - r.top) / r.height)),
        },
      ],
      measurement_confirmed: false,
    });
  }
  async function mask(file) {
    setError("");
    if (!file) return;
    if (file.size > 2_000_000) {
      setError("Use a foreground mask smaller than 2 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () =>
      update({ occlusion_mask_base64: String(reader.result).split(",")[1] });
    reader.onerror = () => setError("The mask could not be read");
    reader.readAsDataURL(file);
  }
  return (
    <section className="protected-editor">
      <div className="protected-title">
        <ShieldCheck size={20} />
        <div>
          <h3>Place the actual piece.</h3>
          <p>
            Measured beta · AI edits contact areas, while seller cutouts stay
            protected.
          </p>
        </div>
      </div>
      {(!capabilities?.enabled || !capabilities?.perception_configured) && (
        <p className="ws-notice">
          Measured placement is not activated on this server yet. You can
          prepare the calibration; rendering needs a configured
          detection/segmentation service and image provider.
        </p>
      )}
      <p className="protected-instructions">
        Mark a visible rectangle on the floor, in order:{" "}
        <strong>far left → far right → near right → near left</strong>. Measure
        its real width and depth. The rectangle can be smaller than the whole
        room.
      </p>
      {photo ? (
        <>
          <div
            className="protected-calibration"
            style={{ aspectRatio: natural.width + "/" + natural.height }}
            onClick={corner}
            aria-label="Floor calibration image"
          >
            <img
              src={photo}
              alt="Your room for measured floor calibration"
              onLoad={(e) =>
                setNatural({
                  width: e.currentTarget.naturalWidth,
                  height: e.currentTarget.naturalHeight,
                })
              }
            />
            <svg
              viewBox="0 0 1000 1000"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              {value.floor_quad.length >= 3 && (
                <polygon
                  points={value.floor_quad
                    .map((p) => `${p.x * 1000},${p.y * 1000}`)
                    .join(" ")}
                />
              )}{" "}
              {value.floor_quad.map((p, i) => (
                <g key={i}>
                  <circle cx={p.x * 1000} cy={p.y * 1000} r="15" />
                  <text x={p.x * 1000 + 22} y={p.y * 1000 - 20}>
                    {i + 1}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          <div className="protected-corner-status">
            <span>{value.floor_quad.length}/4 floor corners marked</span>
            <button
              type="button"
              className="rf-text-button"
              onClick={() =>
                update({ floor_quad: [], measurement_confirmed: false })
              }
            >
              <Undo2 size={14} /> Reset corners
            </button>
          </div>
        </>
      ) : (
        <p className="ws-notice">Upload your room photo first.</p>
      )}
      <details className="protected-coordinates">
        <summary>Enter corner coordinates with the keyboard</summary>
        {Array.from({ length: 4 }, (_, i) => (
          <div className="form-row" key={i}>
            {["x", "y"].map((axis) => (
              <label key={axis}>
                Corner {i + 1} · {axis} %
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={
                    value.floor_quad[i]
                      ? Math.round(value.floor_quad[i][axis] * 1000) / 10
                      : ""
                  }
                  onChange={(e) => {
                    const points = Array.from(
                      { length: Math.max(i + 1, value.floor_quad.length) },
                      (_, j) => value.floor_quad[j] || { x: 0, y: 0 },
                    );
                    points[i] = {
                      ...points[i],
                      [axis]: Number(e.target.value) / 100,
                    };
                    update({
                      floor_quad: points,
                      measurement_confirmed: false,
                    });
                  }}
                />
              </label>
            ))}
          </div>
        ))}
      </details>
      <div className="form-row">
        <label>
          <Ruler size={14} /> Measured width · cm
          <input
            aria-label="Measured floor width"
            type="number"
            min="21"
            max="3000"
            value={value.floor_width_cm}
            onChange={(e) =>
              update({
                floor_width_cm: Number(e.target.value),
                measurement_confirmed: false,
              })
            }
          />
        </label>
        <label>
          Measured depth · cm
          <input
            aria-label="Measured floor depth"
            type="number"
            min="21"
            max="3000"
            value={value.floor_depth_cm}
            onChange={(e) =>
              update({
                floor_depth_cm: Number(e.target.value),
                measurement_confirmed: false,
              })
            }
          />
        </label>
      </div>
      <label className="consent">
        <input
          type="checkbox"
          checked={value.measurement_confirmed}
          onChange={(e) => update({ measurement_confirmed: e.target.checked })}
        />{" "}
        I measured this floor rectangle. An image alone cannot establish
        real-world scale.
      </label>
      <div className="protected-products">
        {assets.map((a) => {
          const p = value.placements.find((p) => p.asset_id === a.id);
          if (!p) return null;
          const change = (patch) =>
            update({
              placements: value.placements.map((q) =>
                q.asset_id === a.id ? { ...q, ...patch } : q,
              ),
            });
          return (
            <article key={a.id}>
              <strong>{a.name}</strong>
              <small>
                {a.width_cm} × {a.depth_cm} cm footprint · photographed views
                only
              </small>
              <label>
                Photographed view
                <select
                  aria-label={"Photographed view for " + a.name}
                  value={p.view}
                  onChange={(e) => change({ view: e.target.value })}
                >
                  {["front", "left", "right", "angled", "top"].map((view) => (
                    <option key={view} value={view}>
                      {view === "top" ? "Top-down · rugs" : view}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-row">
                <label>
                  Across floor · {Math.round(p.u * 100)}%
                  <input
                    aria-label={"Across floor for " + a.name}
                    type="range"
                    min="1"
                    max="99"
                    value={Math.round(p.u * 100)}
                    onChange={(e) =>
                      change({ u: Number(e.target.value) / 100 })
                    }
                  />
                </label>
                <label>
                  Front edge depth · {Math.round(p.v * 100)}%
                  <input
                    aria-label={"Floor depth for " + a.name}
                    type="range"
                    min="1"
                    max="99"
                    value={Math.round(p.v * 100)}
                    onChange={(e) =>
                      change({ v: Number(e.target.value) / 100 })
                    }
                  />
                </label>
              </div>
            </article>
          );
        })}
      </div>
      <label>
        Approximate light direction
        <select
          aria-label="Light direction"
          value={value.light_dx < 0 ? "right" : "left"}
          onChange={(e) =>
            update({ light_dx: e.target.value === "left" ? 0.3 : -0.3 })
          }
        >
          <option value="left">
            Light from the left · shadows to the right
          </option>
          <option value="right">
            Light from the right · shadows to the left
          </option>
        </select>
      </label>
      <details className="protected-foreground">
        <summary>Optional: preserve foreground objects</summary>
        <p>
          Upload a binary mask at the working room size (longest size at most
          1280 × 960). White retains original foreground objects; black allows
          products behind them. A mask with wrong dimensions is rejected.
        </p>
        <input
          aria-label="Foreground occlusion mask"
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={(e) => mask(e.target.files[0])}
        />
        {value.occlusion_mask_base64 && (
          <button
            type="button"
            className="rf-text-button"
            onClick={() => update({ occlusion_mask_base64: undefined })}
          >
            Remove foreground mask
          </button>
        )}
      </details>
      {cacheId && (
        <label className="consent">
          <input
            type="checkbox"
            checked={!!value.reuse_design_id}
            onChange={(e) =>
              update({
                reuse_design_id: e.target.checked ? cacheId : undefined,
              })
            }
          />{" "}
          Reuse the last cleaned room for this project. Room photo and provider
          must match.
        </label>
      )}
      <small className="protected-explanation">
        A fresh workflow reserves three beta attempt slots; cached cleanup uses
        one. Failed attempts count. This preserves transformed product pixels,
        not unseen geometry or a physical-fit guarantee.
      </small>
      {error && (
        <p className="ws-notice error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
