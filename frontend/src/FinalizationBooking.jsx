import React, { useEffect, useRef, useState } from "react";
import { Download, CalendarCheck, FileText } from "lucide-react";
import { api, API, money } from "./workspace-api";
import "./finalization.css";

function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default function FinalizationBooking({ design, projectId }) {
  const [open, setOpen] = useState(false), [summary, setSummary] = useState(null),
    [busy, setBusy] = useState(false), [error, setError] = useState(""),
    [booking, setBooking] = useState(null);
  const key = useRef(crypto.randomUUID());
  useEffect(() => {
    let live = true;
    if (open && projectId) {
      setBusy(true); setError("");
      api(`/api/workspace/projects/${projectId}/finalizations/preview`, "POST", { design_id: design.id })
        .then(data => { if (live) setSummary(data); })
        .catch(e => { if (live) setError(e.message); })
        .finally(() => { if (live) setBusy(false); });
    }
    return () => { live = false; };
  }, [open, projectId, design.id]);
  const items = design.quote.items;
  async function downloadImage() {
    setError(""); setBusy(true);
    try {
      const response = await fetch(API + design.image_url, { credentials: "include" });
      if (!response.ok) throw Error("Could not download this image. Please retry.");
      const bitmap = await createImageBitmap(await response.blob());
      const canvas = document.createElement("canvas"), context = canvas.getContext("2d");
      const width = Math.max(bitmap.width, 1000), scale = width / bitmap.width;
      canvas.width = width; canvas.height = Math.round(bitmap.height * scale) + 135 + items.length * 58;
      context.fillStyle = "#fcfaf6"; context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(bitmap, 0, 0, width, Math.round(bitmap.height * scale));
      const start = Math.round(bitmap.height * scale) + 38;
      context.fillStyle = "#263e30"; context.font = "bold 24px sans-serif";
      context.fillText("Roomform · Design " + design.id, 24, start);
      context.font = "18px sans-serif";
      context.fillText("Selected product references · availability and final fit require confirmation", 24, start + 30);
      items.forEach((item, index) => {
        const y = start + 66 + index * 58;
        context.fillText((index + 1) + ". " + item.name.slice(0, 75), 24, y);
        context.fillText("Item code: " + item.asset_id, 24, y + 24);
      });
      const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
      if (!blob) throw Error("Image export failed. Please retry.");
      saveBlob(blob, `roomform-${design.id}-with-item-codes.png`);
      bitmap.close();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  function downloadManifest() {
    saveBlob(new Blob([JSON.stringify({ design_id: design.id, exported_at: new Date().toISOString(), currency: design.quote.currency, items, note: "Selected references, not stock reservation or confirmation of AI product identity." }, null, 2)], { type: "application/json" }), `roomform-${design.id}-items.json`);
  }
  async function submit(e) {
    e.preventDefault(); const form = new FormData(e.currentTarget);
    setBusy(true); setError("");
    try {
      const result = await api(`/api/workspace/projects/${projectId}/finalizations`, "POST", {
        design_id: design.id, phone: form.get("phone"), address: form.get("address"),
        preferred_date: form.get("preferred_date") || "", consent: form.get("consent") === "on", idempotency_key: key.current,
      });
      setBooking(result);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  const snapshot = booking?.snapshot || summary;
  return <section className="finalization-panel" aria-label="Design export and finalization">
    <h3>Keep the design. Bring it to life.</h3>
    <p>Your download includes the design ID and every selected item code so our team can trace the exact pieces.</p>
    <div className="finalization-actions">
      <button className="rf-text-button" disabled={busy} onClick={downloadImage}><Download size={16}/> Download image with item codes</button>
      <button className="rf-text-button" onClick={downloadManifest}><FileText size={16}/> Download item details</button>
    </div>
    <details className="finalization-codes"><summary>Selected item codes ({items.length})</summary>{items.map(item => <p key={item.asset_id}>{item.name}<br/><code>{item.asset_id}</code></p>)}</details>
    {!open && <button className="rf-primary" onClick={() => setOpen(true)}><CalendarCheck size={17}/> Book for finalization</button>}
    {open && !projectId && <p role="status">Save this design to a project before booking finalization.</p>}
    {open && projectId && <>
      <h4>{booking ? "Finalization request saved" : "Review your finalization estimate"}</h4>
      {busy && !snapshot && <p role="status">Checking current prices, stock and seller lead times…</p>}
      {snapshot && <>
        <div className="finalization-table-wrap"><table><caption>Selected inventory at the time of this estimate</caption><thead><tr><th>Item / code</th><th>Qty</th><th>Stock</th><th>Ready + delivery</th><th>Amount</th></tr></thead><tbody>{snapshot.items.map(item => <tr key={item.asset_id}><td>{item.name}<code>{item.asset_id}</code></td><td>{item.quantity}</td><td>{item.stock}</td><td>{item.ready_min_days == null ? "Not configured" : `${item.ready_min_days}–${item.ready_max_days} + ${item.delivery_min_days}–${item.delivery_max_days} days`}</td><td>{money(item.subtotal, snapshot.currency)}</td></tr>)}</tbody></table></div>
        <dl className="finalization-totals">{[["Project budget",snapshot.budget],["Products",snapshot.items_subtotal],["Estimated labor / installation",snapshot.labor],["Finalization / service charge",snapshot.service_charge],["Estimated total",snapshot.total]].map(([label,value]) => <div key={label}><dt>{label}</dt><dd>{value == null ? "Not configured" : money(value,snapshot.currency)}</dd></div>)}</dl>
        <p><strong>Estimated completion: {snapshot.min_days == null ? "Awaiting lead times" : `${snapshot.min_days}–${snapshot.max_days} days`}</strong></p>
        <p className="photo-guidance">This is a draft agreement for review. Stock is checked now and is not reserved. Dates and costs require confirmation before work or purchases begin.</p>
        {!!snapshot.issues?.length && <div className="ws-notice error" role="status"><strong>Needs confirmation before booking</strong><ul>{snapshot.issues.map((issue,index) => <li key={index}>{typeof issue === "string" ? issue : JSON.stringify(issue)}</li>)}</ul></div>}
      </>}
      {booking ? <div role="status"><p>Request {booking.id} · Email: {booking.email_status}. Keep the PDF for your appointment.</p><a className="rf-primary" href={API + booking.pdf_url} download><Download size={16}/> Download agreement PDF</a></div> : snapshot && <form onSubmit={submit}>
        <label>Contact phone<input name="phone" type="tel" required minLength={6} maxLength={40}/></label>
        <label>Project / delivery address<textarea name="address" required minLength={10} maxLength={500}/></label>
        <label>Preferred appointment date<input name="preferred_date" type="date"/></label>
        <label className="consent"><input name="consent" type="checkbox" required/> I request finalization and agree to share this design, contact details and delivery address with the team. I understand this draft does not confirm payment, reserve stock or authorize work.</label>
        <button className="rf-primary" disabled={busy || !!snapshot.issues?.length}>{busy ? "Saving your request…" : "Confirm finalization request"}</button>
      </form>}
    </>}
    {error && <p className="ws-notice error" role="alert">{error}</p>}
  </section>;
}

export function SavedFinalizations({ projectId }) {
  const [rows, setRows] = useState([]), [error, setError] = useState(""), [loading, setLoading] = useState(true);
  useEffect(() => { let live = true; setLoading(true); setError(""); api(`/api/workspace/projects/${projectId}/finalizations`).then(data => { if(live) setRows(data); }).catch(e => { if(live) setError(e.message); }).finally(() => { if(live) setLoading(false); }); return () => {live=false}; }, [projectId]);
  return <section className="finalization-panel"><h3>Saved finalization requests</h3>{loading && <p role="status">Loading requests…</p>}{error && <p role="alert">{error}</p>}{!loading && !error && !rows.length && <p>No finalization requests yet. Open a saved design and choose “Book for finalization”.</p>}{rows.map(row => <article className="ws-card" key={row.id}><h4>Request {row.id}</h4><p>Design {row.design_id}</p><p>{money(row.snapshot.total,row.snapshot.currency)} · {row.snapshot.min_days}–{row.snapshot.max_days} days · Email {row.email_status}</p><a className="rf-text-button" href={API+row.pdf_url} download>Download agreement PDF</a></article>)}</section>;
}
