import React from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Upload,
  Check,
  Plus,
  Sparkles,
  Layers,
  ShoppingBag,
  Clock,
  MapPin,
  LayoutGrid,
  LoaderCircle,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";

import { AccountGate } from "../Workspace";

import ProtectedPlacement from "../ProtectedPlacement";
import { inspirationCategories } from "../DesignDiscovery";

import RoomResult from "../RoomResult";

import { media, money } from "../app/api";

export default function StudioPage({
  aiConsent,
  area,
  assets,
  autoSelect,
  brief,
  budgetConfirmed,
  chooseFile,
  cleanupCacheId,
  clientLocation,
  condition,
  consultation,
  createPlan,
  currency,
  design,
  file,
  findLocal,
  generate,
  geoBusy,
  invalidate,
  investment,
  loading,
  local,
  model,
  models,
  nav,
  navigate,
  page,
  placementCapabilities,
  placementSpec,
  plan,
  planning,
  preference,
  preview,
  productGrid,
  projects,
  protectedMode,
  quote,
  refineOpen,
  refresh,
  room,
  selected,
  selectedAssets,
  setAiConsent,
  setArea,
  setAutoSelect,
  setBrief,
  setBudgetConfirmed,
  setCheckoutOpen,
  setCleanupCacheId,
  setConsultSent,
  setCurrency,
  setDesign,
  setInvestment,
  setLead,
  setModel,
  setPlacementSpec,
  setPreference,
  setProtectedMode,
  setRefineOpen,
  setRoom,
  setSelected,
  setStyle,
  studioRef,
  style,
  workspace,
}) {
  return (
    <AccountGate>
      <main className="rf-studio" ref={studioRef}>
        <div className="rf-page-heading">
          <span className="rf-kicker">
            <Sparkles size={14} /> YOUR PERSONAL DESIGN STUDIO
          </span>
          <h1>Design your room</h1>
          <p>
            Upload a room photo, confirm your budget, then choose the furniture
            and style you want to explore.
          </p>
        </div>
        <nav className="studio-journey" aria-label="Design steps">
          {[
            ["Your room", !!file, ".rf-workspace"],
            ["Budget & pieces", budgetConfirmed, ".rf-investment"],
            ["Create your design", !!design, ".rf-settings"],
            ["Shop & connect", !!design, ".rf-budget"],
          ].map(([name, done, target], i) => (
            <button
              key={name}
              className={done ? "complete" : ""}
              onClick={() => {
                if (target === ".rf-investment" || target === ".rf-settings")
                  setRefineOpen(true);
                setTimeout(
                  () =>
                    document.querySelector(target)?.scrollIntoView({
                      behavior: "smooth",
                      block: "start",
                    }),
                  40,
                );
              }}
            >
              <span>
                {done ? <Check size={16} /> : String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <strong>{name}</strong>
                <small>
                  {done
                    ? "Ready"
                    : i === 0
                      ? "Start with a photo"
                      : i === 1
                        ? "Choose budget and condition"
                        : i === 2
                          ? "Review your room design"
                          : "Bring it home"}
                </small>
              </div>
              <ChevronRight size={16} />
            </button>
          ))}
        </nav>
        <div className="ws-active-project">
          <label>
            Save previews to
            <select
              value={workspace.activeId}
              onChange={(e) => {
                workspace.select(e.target.value);
                setDesign(null);
                setConsultSent(false);
              }}
            >
              <option value="">Choose a project</option>
              {workspace.projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="rf-text-button"
            onClick={() => navigate("projects")}
          >
            Create / manage projects <ArrowUpRight size={16} />
          </button>
        </div>
        <div className="rf-studio-layout">
          <section className="rf-workspace">
            <div className="rf-card-heading">
              <h3>
                <span>01</span>{" "}
                {design ? "Your new perspective" : "Your starting point"}
              </h3>
              <span>{design ? "Your concept is ready" : "Let’s begin"}</span>
            </div>
            {design ? (
              <RoomResult
                key={design.id}
                projectId={workspace.activeId}
                design={design}
                assets={assets}
                models={models}
                onRoomChange={chooseFile}
                onUpdated={async (d) => {
                  setDesign(d);
                  setSelected(d.quote.items.map((i) => i.asset_id));
                  await workspace.refresh();
                }}
              />
            ) : (
              <div
                className={"rf-canvas " + (preview ? "filled" : "")}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (!loading) chooseFile(e.dataTransfer.files[0]);
                }}
              >
                {preview ? (
                  <img src={preview} alt="Your actual room photograph" />
                ) : (
                  <div className="rf-empty-room">
                    <div className="rf-upload-icon">
                      <Upload size={28} />
                    </div>
                    <h3>Start with the room you have.</h3>
                    <p>
                      Upload a clear photograph.
                      <br />
                      Your seller’s actual products guide the design.
                    </p>
                    <label className="rf-primary">
                      Upload room photo <Plus size={16} />
                      <input
                        type="file"
                        hidden
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => chooseFile(e.target.files[0])}
                      />
                    </label>
                    <small>JPG, PNG, WEBP · up to 12 MB</small>
                  </div>
                )}
                {preview && !loading && (
                  <label className="rf-replace">
                    <Upload size={13} /> Change photo
                    <input
                      type="file"
                      hidden
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(e) => chooseFile(e.target.files[0])}
                    />
                  </label>
                )}
                {loading && (
                  <div className="rf-rendering" role="status">
                    <LoaderCircle className="spin" size={32} />
                    <h3>Preparing your room.</h3>
                    <p>
                      {model === "composite"
                        ? "Arranging your actual product photographs…"
                        : "Matching the room with the seller’s multi-angle product references…"}
                    </p>
                  </div>
                )}
              </div>
            )}
            {design && (
              <div className="rf-render-note">
                <strong>
                  {design.render_mode === "protected_placement"
                    ? "Measured product-protected visualization"
                    : design.render_mode === "ai_reference"
                      ? "AI-generated visualization"
                      : "Illustrative product composite"}
                </strong>
                <p>{design.limitations?.join(" · ")}</p>
                <a
                  href={media(design.image_url)}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open full image <ArrowUpRight size={13} />
                </a>
              </div>
            )}
            <details
              className={"studio-refine " + (!design ? "initial" : "")}
              open={refineOpen}
              onToggle={(e) => setRefineOpen(e.currentTarget.open)}
            >
              <summary>
                <div>
                  <strong>Refine your design</strong>
                  <span>
                    Budget, style, product preferences & creative engine
                  </span>
                </div>
                <SlidersHorizontal size={18} />
              </summary>
              <section className="rf-investment">
                <div>
                  <span className="rf-kicker">
                    YOUR BUDGET. YOUR KIND OF HOME.
                  </span>
                  <h3>
                    <span className="budget-step">02</span> Beautiful, within
                    your budget.
                  </h3>
                  <p>
                    Confirm your budget and condition preference. Catalog
                    matching chooses in-stock references; your selected AI model
                    reimagines the room.
                  </p>
                </div>
                <fieldset disabled={loading || planning}>
                  <div className="form-row three">
                    <label>
                      Estimated room investment
                      <input
                        type="number"
                        min="1"
                        max="10000000"
                        step="0.01"
                        value={investment}
                        onChange={(e) => {
                          setInvestment(e.target.value);
                          setBudgetConfirmed(false);
                          invalidate();
                        }}
                      />
                      <input
                        className="budget-range"
                        aria-label="Adjust room investment"
                        type="range"
                        min={currency === "PKR" ? 25000 : 100}
                        max={currency === "PKR" ? 2000000 : 10000}
                        step={currency === "PKR" ? 5000 : 50}
                        value={Math.min(
                          currency === "PKR" ? 2000000 : 10000,
                          Math.max(
                            currency === "PKR" ? 25000 : 100,
                            Number(investment) || 0,
                          ),
                        )}
                        onChange={(e) => {
                          setInvestment(e.target.value);
                          setBudgetConfirmed(false);
                          invalidate();
                        }}
                      />
                    </label>
                    <label>
                      Currency
                      <select
                        value={currency}
                        onChange={(e) => {
                          setCurrency(e.target.value);
                          setBudgetConfirmed(false);
                          invalidate();
                        }}
                      >
                        <option>USD</option>
                        <option>PKR</option>
                        <option>GBP</option>
                        <option>EUR</option>
                      </select>
                    </label>
                    <label>
                      Furniture & décor
                      <select
                        value={preference}
                        onChange={(e) => {
                          setPreference(e.target.value);
                          setSelected([]);
                          invalidate();
                        }}
                      >
                        <option value="either">New & pre-loved</option>
                        <option value="new">New only</option>
                        <option value="used">Pre-loved only</option>
                      </select>
                    </label>
                  </div>
                  <div className="form-row">
                    <label>
                      How to furnish
                      <select
                        value={autoSelect ? "auto" : "manual"}
                        onChange={(e) => {
                          setAutoSelect(e.target.value === "auto");
                          setSelected([]);
                          invalidate();
                        }}
                      >
                        <option value="auto">Choose products for me</option>
                        <option value="manual">
                          I’ll choose products myself
                        </option>
                      </select>
                    </label>
                    <label className="consent">
                      <input
                        type="checkbox"
                        checked={budgetConfirmed}
                        onChange={(e) => setBudgetConfirmed(e.target.checked)}
                      />{" "}
                      I confirm this estimate ceiling for items and labor.
                      Shipping, taxes and structural work are extra.
                    </label>
                  </div>
                  <button
                    className="rf-primary"
                    onClick={createPlan}
                    disabled={!budgetConfirmed || !investment}
                  >
                    {planning ? (
                      <LoaderCircle className="spin" size={16} />
                    ) : (
                      <Sparkles size={16} />
                    )}{" "}
                    Confirm budget & find my pieces
                  </button>
                  <button
                    className="rf-text-button"
                    style={{ marginLeft: 18 }}
                    onClick={findLocal}
                    disabled={geoBusy}
                  >
                    <MapPin size={14} />
                    {geoBusy
                      ? "Finding location…"
                      : clientLocation
                        ? "Delivery location set · clear"
                        : "Match delivery near me"}
                  </button>
                  {plan && (
                    <div className="rf-plan-result" role="status">
                      <strong>
                        {plan.asset_ids.length} in-stock references ·{" "}
                        {money(plan.quote.total, currency)} estimated ·{" "}
                        {money(plan.remaining_budget, currency)} remaining
                      </strong>
                      <p>
                        {plan.missing_categories.length
                          ? "Partial proposal — no affordable matching " +
                            plan.missing_categories.join(", ") +
                            "."
                          : "Your reference selection is ready."}{" "}
                        Verify physical fit with your designer. Inventory is not
                        reserved.
                      </p>
                    </div>
                  )}
                </fieldset>
              </section>
              <fieldset disabled={loading} className="rf-settings">
                <div className="rf-card-heading">
                  <h3>
                    <span>03</span> Make it feel like you
                  </h3>
                  <Sparkles size={17} />
                </div>
                <div className="rf-style-options">
                  {[
                    ["minimalist", "Quiet minimal"],
                    ["modern", "Soft modern"],
                    ["mid-century", "Mid-century"],
                    ["scandinavian", "Scandinavian"],
                  ].map(([id, name]) => (
                    <button
                      key={id}
                      className={style === id ? "active" : ""}
                      onClick={() => {
                        setStyle(id);
                        invalidate();
                      }}
                    >
                      <span className={"rf-swatch " + id} />
                      {name}
                      {style === id && <Check size={13} />}
                    </button>
                  ))}
                </div>
                <div className="form-row">
                  <label>
                    Room type
                    <select
                      value={room}
                      onChange={(e) => {
                        setRoom(e.target.value);
                        invalidate();
                      }}
                    >
                      {inspirationCategories.map(([id, label]) => (
                        <option key={id} value={id}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Room area · m²
                    <input
                      type="number"
                      min="1"
                      max="1000"
                      value={area}
                      onChange={(e) => {
                        setArea(e.target.value);
                        invalidate();
                      }}
                    />
                  </label>
                </div>
                {!["living", "bedroom", "office"].includes(room) && (
                  <p className="ws-notice">
                    Explore ideas and prepare a brief for this space. A local
                    installation estimate is needed before budgeted rendering;
                    plumbing, structural work and landscaping construction are
                    quoted separately.
                  </p>
                )}
                <label>
                  Tell the AI what you have in mind
                  <textarea
                    placeholder="A warm, airy room with natural materials. Keep the windows and create a cozy reading corner…"
                    maxLength={1200}
                    value={brief}
                    onChange={(e) => {
                      setBrief(e.target.value);
                      setDesign(null);
                      setLead(null);
                    }}
                  />
                  <small>
                    Architecture and product photos guide the AI. Fit and
                    product identity still need your review.
                  </small>
                </label>
                <div className="rf-model-label">
                  Choose your creative engine <Sparkles size={13} />
                </div>
                <div className="rf-engine-options">
                  {models.map((m) => (
                    <button
                      key={m.id}
                      className={model === m.id ? "active" : ""}
                      disabled={!m.available}
                      onClick={() => {
                        setCleanupCacheId("");
                        setPlacementSpec((s) => ({
                          ...s,
                          reuse_design_id: undefined,
                        }));
                        setModel(m.id);
                        setAiConsent(false);
                        setDesign(null);
                        setLead(null);
                      }}
                    >
                      <span>
                        {m.id === "composite" ? (
                          <Layers size={17} />
                        ) : (
                          <Sparkles size={17} />
                        )}
                        <strong>
                          {m.id === "composite"
                            ? "Photo layout"
                            : m.id === "openai"
                              ? "GPT Image"
                              : "Gemini Image"}
                        </strong>
                        {model === m.id && <Check size={15} />}
                      </span>
                      <small>
                        {m.available
                          ? m.id === "composite"
                            ? "Local · exact product-image overlays"
                            : "AI · room + product references"
                          : m.reason}
                      </small>
                    </button>
                  ))}
                </div>
                {model !== "composite" && (
                  <>
                    <label className="consent protected-workflow-choice">
                      <input
                        type="checkbox"
                        checked={protectedMode}
                        onChange={(e) => {
                          setProtectedMode(e.target.checked);
                          setDesign(null);
                        }}
                      />
                      <span>
                        <strong>Protect actual products · measured beta</strong>
                        Use approved cutouts, measured floor placement and
                        restricted AI edits.
                      </span>
                    </label>
                    {protectedMode && (
                      <ProtectedPlacement
                        photo={preview}
                        assets={selectedAssets}
                        value={placementSpec}
                        onChange={setPlacementSpec}
                        capabilities={placementCapabilities}
                        cacheId={cleanupCacheId}
                      />
                    )}
                  </>
                )}
                {model !== "composite" && (
                  <label className="consent">
                    <input
                      type="checkbox"
                      checked={aiConsent}
                      onChange={(e) => setAiConsent(e.target.checked)}
                    />{" "}
                    I agree to send my room and selected product photos to this
                    AI provider. Measured placement also shares the room with
                    the configured detection/segmentation service.
                  </label>
                )}
                <button
                  className="rf-primary rf-generate"
                  onClick={generate}
                  disabled={
                    loading ||
                    !workspace.active ||
                    !budgetConfirmed ||
                    !file ||
                    !selected.length ||
                    !area ||
                    (autoSelect && !plan) ||
                    (model !== "composite" && !aiConsent) ||
                    (protectedMode &&
                      model !== "composite" &&
                      (!placementCapabilities?.enabled ||
                        !placementCapabilities?.perception_configured ||
                        placementSpec.floor_quad.length !== 4 ||
                        !placementSpec.measurement_confirmed ||
                        placementSpec.placements.length !== selected.length))
                  }
                >
                  {loading ? (
                    <LoaderCircle className="spin" size={18} />
                  ) : (
                    <Sparkles size={18} />
                  )}{" "}
                  {loading
                    ? "Creating your room…"
                    : design
                      ? "Explore another variation"
                      : model === "composite"
                        ? "Create photo layout"
                        : "Reimagine my room"}{" "}
                  <ArrowRight size={17} />
                </button>
                <small className="rf-local-notice">
                  {model === "composite"
                    ? "Local product staging. No AI generation or external photo sharing."
                    : protectedMode
                      ? "Measured staging uses up to three external calls. Seller cutouts are restored after restricted harmonization; verify scale and placement."
                      : "One generation request. AI may alter or omit reference products; verify before purchasing."}
                </small>
              </fieldset>
            </details>
          </section>
          <aside className="rf-studio-side">
            <section className="rf-product-picker">
              <div className="rf-card-heading">
                <h3>
                  <span>04</span> Your real-product edit
                </h3>
                <span>{selected.length}/8</span>
              </div>
              <p>
                Choose available seller products. Inspect their actual
                photographs before adding them to your room.
              </p>
              <button
                className="rf-text-button"
                onClick={findLocal}
                disabled={geoBusy}
              >
                <MapPin size={14} />
                {geoBusy
                  ? "Finding nearby pieces…"
                  : local
                    ? "Within 50 km · show all"
                    : "Discover pieces near me"}
              </button>
              {productGrid(
                assets.filter(
                  (a) =>
                    preference === "either" ||
                    (preference === "new"
                      ? a.condition === "new"
                      : a.condition !== "new"),
                ),
              )}
            </section>
            <section className="rf-budget">
              <div className="rf-card-heading">
                <h3>
                  <LayoutGrid size={16} /> Your room, in numbers
                </h3>
                <span>Estimate</span>
              </div>
              {quote ? (
                <>
                  <div className="rf-budget-items">
                    {quote.items.map((i) => (
                      <div key={i.asset_id}>
                        <span>
                          {i.name} ×{i.quantity}
                        </span>
                        <strong>{money(i.subtotal, quote.currency)}</strong>
                      </div>
                    ))}
                  </div>
                  <div>
                    <span>Furniture & décor</span>
                    <strong>
                      {money(quote.items_subtotal, quote.currency)}
                    </strong>
                  </div>
                  <div>
                    <span>Labor & installation</span>
                    <strong>{money(quote.labor, quote.currency)}</strong>
                  </div>
                  <div className="rf-budget-total">
                    <span>Estimated investment</span>
                    <strong>{money(quote.total, quote.currency)}</strong>
                  </div>
                  <div className="rf-timeline">
                    <Clock size={16} />
                    <span>Delivery & setup</span>
                    <strong>{quote.timeline_days} days</strong>
                  </div>
                  <small>
                    Selected product references, not verified image contents.
                    Excludes taxes and shipping; availability and site costs may
                    vary.
                  </small>
                  <button
                    className="rf-primary"
                    onClick={() => navigate("consult")}
                  >
                    Make this room real <ArrowUpRight size={16} />
                  </button>
                  <button
                    className="rf-text-button"
                    onClick={() => {
                      setSelected(quote.items.map((i) => i.asset_id));
                      setCheckoutOpen(true);
                      navigate("marketplace");
                    }}
                  >
                    Request products in this design <ShoppingBag size={16} />
                  </button>
                </>
              ) : (
                <>
                  <p>
                    {selected.length} pieces selected. Generate your room to see
                    installation costs and a timeline.
                  </p>
                  {selectedAssets.map((a) => (
                    <div key={a.id}>
                      <span>{a.name}</span>
                      <strong>{money(a.price, a.currency)}</strong>
                    </div>
                  ))}
                </>
              )}
            </section>
          </aside>
        </div>
        {consultation()}
      </main>
    </AccountGate>
  );
}
