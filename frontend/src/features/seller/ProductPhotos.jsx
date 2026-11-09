import React, { useEffect, useState } from "react";
import { call } from "./api";
import ProductPhotoStudio from "../../ProductPhotoStudio";
export default function Photos({ item, token, onUpdate }) {
  const [photos, setPhotos] = useState([]),
    [primary, setPrimary] = useState(""),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  return (
    <section className="vendor-editor-section">
      <h3>Product photographs</h3>
      <p>
        Upload replacement photographs, review each cutout, then save the
        complete new photo set.
      </p>
      <ProductPhotoStudio
        token={token}
        photos={photos}
        onChange={setPhotos}
        primaryId={primary}
        onPrimary={setPrimary}
      />
      <button
        className="rf-primary"
        disabled={
          busy || !photos.length || photos.some((p) => !p.approved) || !primary
        }
        onClick={async () => {
          setBusy(true);
          try {
            await call(
              "/api/seller/listings/" + item.id + "/photos",
              token,
              "POST",
              {
                photo_ids: photos.map((p) => p.id),
                image_url: photos.find((p) => p.id === primary).cutout_url,
              },
            );
            setMessage("Photographs updated.");
            await onUpdate();
          } catch (e) {
            setMessage(e.message);
          } finally {
            setBusy(false);
          }
        }}
      >
        Save replacement photographs
      </button>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
