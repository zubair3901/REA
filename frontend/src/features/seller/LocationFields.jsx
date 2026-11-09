import React, { useEffect, useState } from "react";
import { MapPin } from "lucide-react";
export default function LocationFields({ item = {} }) {
  const [location, setLocation] = useState({
      latitude: item.latitude ?? "",
      longitude: item.longitude ?? "",
    }),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  function locate() {
    setMessage("");
    if (!navigator.geolocation) {
      setMessage(
        "Location is not available. Enter coordinates manually below.",
      );
      return;
    }
    setBusy(true);
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setLocation({
          latitude: p.coords.latitude,
          longitude: p.coords.longitude,
        });
        setMessage(
          "Location captured. Accuracy approximately " +
            Math.round(p.coords.accuracy) +
            " metres. Confirm the delivery area below.",
        );
        setBusy(false);
      },
      () => {
        setMessage(
          "Location access was unavailable or denied. You can enter coordinates manually. HTTPS or localhost is required.",
        );
        setBusy(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    );
  }
  return (
    <>
      <div className="vendor-location">
        <button
          type="button"
          className="rf-text-button"
          disabled={busy}
          onClick={locate}
        >
          <MapPin size={17} />
          {busy ? "Finding your location…" : "Use my current location"}
        </button>
        <small>Only requested when you choose this action.</small>
      </div>
      {message && <p role="status">{message}</p>}
      <details
        className="vendor-coordinate-details"
        open={location.latitude === "" || undefined}
      >
        <summary>Warehouse coordinates</summary>
        <div className="vendor-fields">
          {["latitude", "longitude"].map((n) => (
            <label key={n}>
              {n === "latitude" ? "Latitude" : "Longitude"}
              <input
                name={n}
                type="number"
                min={n === "latitude" ? -90 : -180}
                max={n === "latitude" ? 90 : 180}
                step="any"
                required
                value={location[n]}
                onChange={(e) =>
                  setLocation({ ...location, [n]: e.target.value })
                }
              />
            </label>
          ))}
        </div>
      </details>
    </>
  );
}
