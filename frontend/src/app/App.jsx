import React, { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Upload,
  Check,
  Plus,
  Sparkles,
  Layers,
  ShoppingBag,
  MapPin,
  Armchair,
  X,
  Home,
  Images,
  SlidersHorizontal,
  Store,
  MessageCircle,
  Users as UsersIcon,
} from "lucide-react";
import SellerPortal from "../SellerPortal";
import Operations from "../Operations";
import Workspace, {
  useWorkspace,
  AccountGate,
  Consultation,
  Checkout,
} from "../Workspace";
import Professionals from "../Professionals";
import Teams from "../Teams";
// Keep the shared photo-style evaluation position stable.
import "../photography.css";
import { emptyPlacementSpec } from "../ProtectedPlacement";
import { TransformationDemos, DesignFAQ } from "../DesignDiscovery";
import ProductPhotoViewer from "../ProductPhotoViewer";
import "../fonts.css";
import "../redesign.css";
import "../atelier.css";
import "../discovery.css";
import "../polish.css";
import "../friendly.css";
import AppNavigation from "../AppNavigation";
import "../app-home.css";
import "../webapp.css";
import InspirationGallery from "../CuratedInspirations";
import { API, media, money, request } from "./api";
import { pageNames, initialPage } from "./routing";
import AppHeader from "./AppHeader";
import AppFooter from "./AppFooter";
import HomePage from "../pages/HomePage";
import StudioPage from "../pages/StudioPage";
import MarketplacePage from "../pages/MarketplacePage";
export default function App() {
  const workspace = useWorkspace();
  const [inspectAsset, setInspectAsset] = useState(null);
  const [protectedMode, setProtectedMode] = useState(false),
    [placementSpec, setPlacementSpec] = useState(emptyPlacementSpec),
    [placementCapabilities, setPlacementCapabilities] = useState(null),
    [cleanupCacheId, setCleanupCacheId] = useState("");
  useEffect(() => {
    request("/api/placement/capabilities")
      .then((c) => {
        setPlacementCapabilities(c);
        if (c.enabled && c.perception_configured) setProtectedMode(true);
      })
      .catch(() => {});
  }, []);
  const [catalogError, setCatalogError] = useState("");
  const [refineOpen, setRefineOpen] = useState(true);
  const [checkoutOpen, setCheckoutOpen] = useState(false),
    [consultSent, setConsultSent] = useState(false);
  const [page, setPage] = useState(initialPage),
    [mobile, setMobile] = useState(false),
    [assets, setAssets] = useState([]),
    [models, setModels] = useState([]),
    [model, setModel] = useState("composite"),
    [selected, setSelected] = useState([]),
    [file, setFile] = useState(null),
    [preview, setPreview] = useState(""),
    [style, setStyle] = useState("minimalist"),
    [room, setRoom] = useState("living"),
    [area, setArea] = useState(24),
    [brief, setBrief] = useState(""),
    [aiConsent, setAiConsent] = useState(false),
    [design, setDesign] = useState(null),
    [projects, setProjects] = useState([]),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [lead, setLead] = useState(null),
    [leadBusy, setLeadBusy] = useState(false),
    [compare, setCompare] = useState(50),
    [geoBusy, setGeoBusy] = useState(false),
    [local, setLocal] = useState(false),
    [search, setSearch] = useState(""),
    [condition, setCondition] = useState("all");
  const [autoSelect, setAutoSelect] = useState(true),
    [investment, setInvestment] = useState(1500),
    [preference, setPreference] = useState("either"),
    [currency, setCurrency] = useState("USD"),
    [budgetConfirmed, setBudgetConfirmed] = useState(false),
    [plan, setPlan] = useState(null),
    [planning, setPlanning] = useState(false);
  useEffect(() => setRefineOpen(!design), [design?.id]);
  const [clientLocation, setClientLocation] = useState(null);
  const studioRef = useRef(null);
  const photoUrls = useRef([]);
  const refresh = () =>
    request("/api/assets")
      .then((a) => {
        setAssets(a);
        setCatalogError("");
      })
      .catch(() =>
        setCatalogError(
          "The live collection is temporarily unavailable. You can still explore the design experience.",
        ),
      );
  useEffect(() => {
    if (workspace.active) {
      setInvestment(workspace.active.budget);
      setCurrency(workspace.active.currency);
      setPreference(workspace.active.preference);
      setCleanupCacheId("");
      setPlacementSpec(emptyPlacementSpec());
      setDesign(null);
      setPlan(null);
      setSelected([]);
      setBudgetConfirmed(false);
      setConsultSent(false);
    }
  }, [workspace.active?.id]);
  useEffect(() => {
    refresh();
    request("/api/models")
      .then((m) => {
        setModels(m);
        setModel(
          m.find((x) => x.id !== "composite" && x.available)?.id || "composite",
        );
      })
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const u = URL.createObjectURL(file);
    photoUrls.current.push(u);
    setPreview(u);
  }, [file]);
  useEffect(
    () => () => photoUrls.current.forEach((u) => URL.revokeObjectURL(u)),
    [],
  );
  useEffect(() => {
    if (!mobile) return;
    const close = (e) => {
      if (e.key === "Escape") {
        setMobile(false);
        document.querySelector(".atelier-menu-toggle")?.focus();
      }
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [mobile]);
  useEffect(() => {
    const pop = () => {
      setPage(initialPage());
      setMobile(false);
      setError("");
    };
    window.addEventListener("popstate", pop);
    return () => window.removeEventListener("popstate", pop);
  }, []);
  useEffect(() => {
    document.title = pageNames[page] + " · Roomform";
  }, [page]);
  function navigate(p) {
    if (p !== page) {
      const url = new URL(location.href);
      if (p === "discover") url.searchParams.delete("page");
      else url.searchParams.set("page", p);
      if (p !== "projects") url.searchParams.delete("reset");
      history.pushState({}, "", url);
    }
    setPage(p);
    setMobile(false);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function invalidate() {
    setDesign(null);
    setLead(null);
    setPlan(null);
  }
  function chooseFile(f) {
    if (f && f.size > 12 * 1024 * 1024) {
      setError("Please choose an image smaller than 12 MB.");
      return;
    }
    setCleanupCacheId("");
    setPlacementSpec(emptyPlacementSpec());
    setFile(f);
    setDesign(null);
    setLead(null);
  }
  function toggle(id) {
    if (loading) return;
    setAutoSelect(false);
    if (!selected.includes(id) && selected.length >= 8) {
      setError("Choose up to eight products for one room.");
      return;
    }
    setSelected((s) =>
      s.includes(id) ? s.filter((x) => x !== id) : [...s, id],
    );
    invalidate();
  }
  function startWith(item) {
    setStyle(item.style);
    setRoom(item.room);
    setBrief(item.brief);
    invalidate();
    navigate("studio");
  }
  async function findLocal() {
    if (local) {
      setLocal(false);
      setClientLocation(null);
      setSelected([]);
      invalidate();
      refresh();
      return;
    }
    if (!navigator.geolocation) {
      setError("Geolocation is unavailable.");
      return;
    }
    setGeoBusy(true);
    navigator.geolocation.getCurrentPosition(
      async (p) => {
        try {
          setAssets(
            await request(
              "/api/assets?latitude=" +
                p.coords.latitude +
                "&longitude=" +
                p.coords.longitude +
                "&radius_km=50",
            ),
          );
          setLocal(true);
          setClientLocation({
            latitude: p.coords.latitude,
            longitude: p.coords.longitude,
          });
          setSelected([]);
          invalidate();
        } catch (e) {
          setError(e.message);
        } finally {
          setGeoBusy(false);
        }
      },
      () => {
        setError(
          "Location access was unavailable. You can still browse all products.",
        );
        setGeoBusy(false);
      },
      { timeout: 10000 },
    );
  }
  async function generate() {
    setError("");
    if (!budgetConfirmed) {
      setError("Confirm your investment ceiling first.");
      return;
    }
    if (autoSelect && !plan) {
      setError("Confirm your budget and product proposal first.");
      return;
    }
    if (!file || !selected.length) {
      setError("Upload your room and choose at least one product.");
      return;
    }
    if (model !== "composite" && !aiConsent) {
      setError("Please approve photo sharing with the selected AI provider.");
      return;
    }
    setLoading(true);
    setLead(null);
    try {
      if (!workspace.active)
        throw Error("Choose a saved project in My projects first.");
      const f = new FormData();
      Object.entries({
        project_id: workspace.activeId,
        style,
        room_category: room,
        room_area: area,
        asset_ids: JSON.stringify(selected),
        plan_id: plan?.id || "",
        budget_ceiling: investment,
        budget_confirmed: String(budgetConfirmed),
        condition_preference: preference,
        budget_currency: currency,
        model,
        ai_consent: String(aiConsent),
        design_brief: brief,
        pipeline:
          protectedMode && model !== "composite" ? "protected" : "reference",
        placement_spec:
          protectedMode && model !== "composite"
            ? JSON.stringify(placementSpec)
            : "",
      }).forEach(([k, v]) => f.append(k, v));
      f.append("room", file);
      const d = await request("/api/designs", { method: "POST", body: f });
      if (d.render_mode === "protected_placement") setCleanupCacheId(d.id);
      const record = {
        ...d,
        original: preview,
        name: style.charAt(0).toUpperCase() + style.slice(1) + " " + room,
        created: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setDesign(record);
      setProjects((p) => [record, ...p]);
      await workspace.refresh();
      setCompare(50);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  async function capture(e) {
    e.preventDefault();
    setError("");
    setLeadBusy(true);
    try {
      const f = new FormData(e.currentTarget);
      setLead(
        await request("/api/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            design_id: design.id,
            name: f.get("name"),
            email: f.get("email"),
            phone: f.get("phone"),
            consent: true,
          }),
        }),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setLeadBusy(false);
    }
  }
  async function createPlan() {
    setError("");
    setPlanning(true);
    try {
      const p = await request("/api/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...clientLocation,
          budget: Number(investment),
          budget_confirmed: budgetConfirmed,
          currency,
          preference,
          style,
          room_category: room,
          room_area: Number(area),
        }),
      });
      setAutoSelect(true);
      setPlan(p);
      setSelected(p.asset_ids);
      setDesign(null);
      setLead(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setPlanning(false);
    }
  }
  const selectedAssets = selected
    .map((id) => assets.find((a) => a.id === id))
    .filter(Boolean);
  const quote = design?.quote;
  const filtered = assets.filter(
    (a) =>
      (condition === "all" ||
        (condition === "used"
          ? a.condition !== "new"
          : a.condition === "new")) &&
      a.name.toLowerCase().includes(search.toLowerCase()),
  );
  const nav = [
    ["discover", Home, "Discover"],
    ["inspiration", Images, "Inspiration"],
    ["studio", Sparkles, "AI design studio"],
    ["projects", Images, "My projects"],
    ["professionals", UsersIcon, "Local professionals"],
    ["teams", UsersIcon, "For business"],
    ["marketplace", ShoppingBag, "Real furniture"],
    ["partners", Store, "Sell with us"],
    ["consult", MessageCircle, "Talk to a designer"],
    ["operations", SlidersHorizontal, "Operations"],
  ];
  const productGrid = (list) =>
    !list.length ? (
      <div className="collection-empty">
        <Armchair size={30} />
        <div>
          <h3>Great spaces begin with real pieces.</h3>
          <p>
            {catalogError ||
              "Our seller collection is growing. Only approved, in-stock listings with real product photography appear here."}
          </p>
        </div>
        <button className="rf-text-button" onClick={() => navigate("seller")}>
          List your first piece <ArrowUpRight size={16} />
        </button>
      </div>
    ) : (
      <div className="rf-products">
        {list.map((a) => (
          <article key={a.id} className="rf-product-wrapper">
            <button
              className={
                "rf-product " + (selected.includes(a.id) ? "picked" : "")
              }
              disabled={loading}
              onClick={() => toggle(a.id)}
              aria-pressed={selected.includes(a.id)}
            >
              <div className="rf-product-photo">
                <img src={media(a.image_url)} alt={a.name} />
                <span className="rf-product-add">
                  {selected.includes(a.id) ? (
                    <Check size={15} />
                  ) : (
                    <Plus size={15} />
                  )}
                </span>
                {a.condition && a.condition !== "new" && (
                  <span className="rf-preowned">Pre-loved</span>
                )}
              </div>
              <small>
                {a.category} · {a.stock} available · {a.delivery_days} day
                delivery
              </small>
              <strong>{a.name}</strong>
              <span>{money(a.price, a.currency)}</span>
              <small>
                {a.width_cm} × {a.depth_cm} × {a.height_cm} cm · W × D × H
              </small>
              {a.delivery_location && (
                <small>
                  <MapPin size={11} /> {a.delivery_location}
                </small>
              )}
            </button>
            {
              <button
                className="rf-photo-button"
                onClick={() => setInspectAsset(a)}
              >
                <Layers size={13} /> View actual product photos
              </button>
            }
          </article>
        ))}
      </div>
    );
  const consultation = () => (
    <section className="rf-section">
      <AccountGate>
        {workspace.active ? (
          <>
            {consultSent ? (
              <div className="ws-notice">
                Your consultation request is saved. Follow its progress in My
                projects → Orders & requests.
              </div>
            ) : (
              <Consultation
                key={workspace.activeId}
                projectId={workspace.activeId}
                onDone={() => setConsultSent(true)}
              />
            )}
          </>
        ) : (
          <div className="ws-card">
            <h2>Bring your ideas to life.</h2>
            <p>
              Create a project to connect your budget, product choices and
              consultation.
            </p>
            <button className="rf-primary" onClick={() => navigate("projects")}>
              Create a project <ArrowRight size={16} />
            </button>
          </div>
        )}
      </AccountGate>
    </section>
  );
  if (page === "seller" || page === "partners")
    return (
      <div className="rf-shell discovery-theme seller-app">
        <SellerPortal onPublished={refresh} />
      </div>
    );
  return (
    <div className={"rf-shell discovery-theme page-" + page}>
      {inspectAsset && (
        <ProductPhotoViewer
          asset={inspectAsset}
          onClose={() => setInspectAsset(null)}
        />
      )}
      <AppNavigation page={page} navigate={navigate} onDesign={startWith} />
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <AppHeader
        mobile={mobile}
        nav={nav}
        navigate={navigate}
        page={page}
        setMobile={setMobile}
        workspace={workspace}
      />
      <div className="rf-content" id="main-content" tabIndex={-1}>
        {error && (
          <div className="rf-error" role="alert">
            {error}
            <button aria-label="Dismiss error" onClick={() => setError("")}>
              <X size={17} />
            </button>
          </div>
        )}
        {page === "discover" && (
          <HomePage
            assets={assets}
            selected={selected}
            navigate={navigate}
            productGrid={productGrid}
            setInvestment={setInvestment}
            setCurrency={setCurrency}
            setBudgetConfirmed={setBudgetConfirmed}
            setBrief={setBrief}
            invalidate={invalidate}
            startWith={startWith}
          />
        )}
        {page === "inspiration" && (
          <main>
            <InspirationGallery full onSelect={startWith} />
            <TransformationDemos onSelect={startWith} />
            <DesignFAQ />
          </main>
        )}
        {page === "studio" && (
          <StudioPage
            aiConsent={aiConsent}
            area={area}
            assets={assets}
            autoSelect={autoSelect}
            brief={brief}
            budgetConfirmed={budgetConfirmed}
            chooseFile={chooseFile}
            cleanupCacheId={cleanupCacheId}
            clientLocation={clientLocation}
            condition={condition}
            consultation={consultation}
            createPlan={createPlan}
            currency={currency}
            design={design}
            file={file}
            findLocal={findLocal}
            generate={generate}
            geoBusy={geoBusy}
            invalidate={invalidate}
            investment={investment}
            loading={loading}
            local={local}
            model={model}
            models={models}
            nav={nav}
            navigate={navigate}
            page={page}
            placementCapabilities={placementCapabilities}
            placementSpec={placementSpec}
            plan={plan}
            planning={planning}
            preference={preference}
            preview={preview}
            productGrid={productGrid}
            projects={projects}
            protectedMode={protectedMode}
            quote={quote}
            refineOpen={refineOpen}
            refresh={refresh}
            room={room}
            selected={selected}
            selectedAssets={selectedAssets}
            setAiConsent={setAiConsent}
            setArea={setArea}
            setAutoSelect={setAutoSelect}
            setBrief={setBrief}
            setBudgetConfirmed={setBudgetConfirmed}
            setCheckoutOpen={setCheckoutOpen}
            setCleanupCacheId={setCleanupCacheId}
            setConsultSent={setConsultSent}
            setCurrency={setCurrency}
            setDesign={setDesign}
            setInvestment={setInvestment}
            setLead={setLead}
            setModel={setModel}
            setPlacementSpec={setPlacementSpec}
            setPreference={setPreference}
            setProtectedMode={setProtectedMode}
            setRefineOpen={setRefineOpen}
            setRoom={setRoom}
            setSelected={setSelected}
            setStyle={setStyle}
            studioRef={studioRef}
            style={style}
            workspace={workspace}
          />
        )}
        {page === "marketplace" && (
          <MarketplacePage
            checkoutOpen={checkoutOpen}
            condition={condition}
            filtered={filtered}
            findLocal={findLocal}
            geoBusy={geoBusy}
            local={local}
            navigate={navigate}
            productGrid={productGrid}
            search={search}
            selected={selected}
            setCheckoutOpen={setCheckoutOpen}
            setCondition={setCondition}
            setSearch={setSearch}
          />
        )}
        {page === "projects" && (
          <Workspace
            navigate={navigate}
            onDesign={(d) => {
              setDesign({ ...d, name: d.style + " room" });
              setLead(null);
              navigate("studio");
            }}
          />
        )}
        {page === "professionals" && <Professionals />}
        {page === "teams" && <Teams />}
        {page === "operations" && <Operations />}
        {page === "partners" && (
          <main className="rf-partner-wrap">
            <SellerPortal onPublished={refresh} />
          </main>
        )}
        {page === "consult" && (
          <main className="rf-section">
            <div className="rf-page-heading">
              <span className="rf-kicker">FROM CONCEPT TO CONVERSATION</span>
              <h1>
                A little guidance.
                <br />
                <em>A lot of possibility.</em>
              </h1>
              <p>
                Connect your saved project with our team to discuss products,
                budget and next steps.
              </p>
            </div>
            {consultation()}
          </main>
        )}
        <AppFooter navigate={navigate} />
      </div>
    </div>
  );
}
