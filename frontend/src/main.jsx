import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
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
  Armchair,
  LayoutGrid,
  X,
  LoaderCircle,
  Home,
  Images,
  Menu,
  ChevronRight,
  Heart,
  SlidersHorizontal,
  MoveHorizontal,
  Leaf,
  Store,
  MessageCircle,
  Users as UsersIcon,
} from "lucide-react";
import SellerPortal from "./SellerPortal";
import Operations from "./Operations";
import Workspace, {
  WorkspaceProvider,
  useWorkspace,
  AccountGate,
  Consultation,
  Checkout,
} from "./Workspace";
import Professionals from "./Professionals";
import Teams from "./Teams";
import ExperienceHero from "./ExperienceHero";
import ProtectedPlacement, { emptyPlacementSpec } from "./ProtectedPlacement";
import {
  RoomCategories,
  TransformationDemos,
  DesignTools,
  MarketplaceStory,
  DesignFAQ,
  inspirationCategories,
} from "./DesignDiscovery";
import ProductPhotoViewer from "./ProductPhotoViewer";
import RoomResult from "./RoomResult";
import "./fonts.css";
import "./redesign.css";
import "./atelier.css";
import "./discovery.css";
import "./polish.css";
import "./friendly.css";
import AppNavigation from "./AppNavigation";
import { DesignCategories, RedesignPanels } from "./AppHomeSections";
import "./webapp.css";
import InspirationGallery from "./CuratedInspirations";
const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const media = (p) => (p?.startsWith("/") ? API + p : p);
const money = (n, c = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: c }).format(
    Number(n || 0),
  );
async function request(path, options) {
  const r = await fetch(API + path, { ...options, credentials: "include" });
  let d;
  try {
    d = await r.json();
  } catch {
    throw Error(
      "The service returned an unexpected response. Please try again.",
    );
  }
  if (!r.ok)
    throw Error(
      typeof d.detail === "string"
        ? d.detail
        : "Please check your details and try again.",
    );
  return d;
}
const pageNames = {
  discover: "Home",
  inspiration: "Inspiration",
  studio: "Design studio",
  marketplace: "Shop",
  professionals: "Professionals",
  partners: "For sellers",
  seller: "Seller workspace",
  projects: "My projects",
  teams: "For business",
  consult: "Consultation",
  operations: "Operations",
};
function initialPage() {
  const q = new URLSearchParams(location.search);
  return q.has("reset")
    ? "projects"
    : Object.hasOwn(pageNames, q.get("page"))
      ? q.get("page")
      : "discover";
}
function App() {
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
  if (page === "seller" || page === "partners") return <div className="rf-shell discovery-theme seller-app"><SellerPortal onPublished={refresh} /></div>;
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
      <header className="atelier-header">
        <a
          className="rf-logo"
          href="#"
          aria-label="Roomform home"
          onClick={(e) => {
            e.preventDefault();
            navigate("discover");
          }}
        >
          <span className="brand-mark">
            <Layers size={24} />
          </span>
          roomform<span className="rf-logo-dot">.</span>
        </a>
        <nav className="atelier-desktop-nav" aria-label="Main navigation">
          {[
            ["studio", "Design studio"],
            ["inspiration", "Inspiration"],
            ["marketplace", "Shop"],
            ["professionals", "Professionals"],
          ].map(([id, label]) => (
            <button
              key={id}
              aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}
            >
              {label}

            </button>
          ))}
        </nav>
        <div className="atelier-header-actions">
          <button
            className="header-seller"
            onClick={() => navigate("seller")}
          >
            Become a seller <ArrowUpRight size={15} />
          </button>
          <button
            className="header-account"
            onClick={() => navigate("projects")}
          >
            <span className="account-avatar">
              {workspace.user ? (
                workspace.user.name.charAt(0).toUpperCase()
              ) : (
                <UsersIcon size={16} />
              )}
            </span>
            <span>{workspace.user ? "My workspace" : "My projects"}</span>
          </button>
          <button
            className="atelier-menu-toggle"
            aria-expanded={mobile}
            aria-controls="site-menu"
            aria-label={mobile ? "Close menu" : "Open menu"}
            onClick={() => setMobile(!mobile)}
          >
            {mobile ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </header>
      {mobile && (
        <>
          <button
            className="atelier-menu-scrim"
            aria-label="Close navigation"
            onClick={() => setMobile(false)}
          />
          <nav className="atelier-menu" id="site-menu" aria-label="All pages">
            <span className="rf-kicker">MAKE ROOM FOR SOMETHING GOOD</span>
            {nav.map(([id, Icon, label]) => (
              <button
                key={id}
                aria-current={page === id ? "page" : undefined}
                onClick={() => navigate(id)}
              >
                <Icon size={19} />
                {label}
                <ArrowUpRight size={16} />
              </button>
            ))}
          </nav>
        </>
      )}
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
          <>
            <ExperienceHero
              onStart={({ budget, service }) => {
                setInvestment(budget);
                setCurrency("USD");
                setBudgetConfirmed(false);
                setBrief(
                  service === "furniture"
                    ? "Arrange real furniture while preserving the room architecture."
                    : service === "walls"
                      ? "Refresh the wall finishes while preserving existing room architecture."
                      : "Create a warm, carefully coordinated interior with real product references.",
                );
                invalidate();
                navigate("studio");
              }}
              onSellers={() => navigate("seller")}
            />
            <div className="rf-trust">
              <span>
                <Sparkles size={17} /> Reference-guided AI design
              </span>
              <span>
                <ShoppingBag size={17} /> Real products, transparent prices
              </span>
              <span>
                <Leaf size={17} /> New & pre-loved finds
              </span>
            </div>
            <DesignCategories onSelect={startWith} />
            <InspirationGallery
              onSelect={startWith}
              onExplore={() => navigate("inspiration")}
            />
            <RedesignPanels onSelect={startWith} />
            <MarketplaceStory navigate={navigate} />
            <DesignTools navigate={navigate} />
            <section className="rf-section rf-market-teaser">
              <div className="rf-section-heading">
                <div>
                  <h2>
                    Furniture from our sellers
                  </h2>
                </div>
                <button
                  className="rf-text-button"
                  onClick={() => navigate("marketplace")}
                >
                  Explore the collection <ArrowUpRight size={17} />
                </button>
              </div>
              <p className="rf-subtle">
                Discover pieces photographed by real sellers. Their original
                angles, condition and current price stay connected to the
                listing.
              </p>
              {productGrid(assets.slice(0, 4))}
              {selected.length > 0 && (
                <button
                  className="rf-text-button rf-mobile-cta"
                  onClick={() => navigate("studio")}
                >
                  Use selected pieces in my room <ArrowRight size={16} />
                </button>
              )}
            </section>
            <section className="rf-premium">
              <div>
                <h2>Plan one project at a time</h2>
                <p>
                  Explore your space, source real products, and meet the people
                  who can bring it together.
                </p>
                <small>
                  One-time image packages launch with AI. Product previews and
                  project planning are available now.
                </small>
              </div>
              <div>
                <strong>
                  $3–$5 <span>USD / project package</span>
                </strong>
                <p>3 or 6 images · products and services priced separately</p>
                <button
                  className="rf-primary"
                  onClick={() => navigate("projects")}
                >
                  Start your project <ArrowUpRight size={16} />
                </button>
                <button
                  className="rf-text-button"
                  onClick={() => navigate("teams")}
                >
                  Explore business plans →
                </button>
              </div>
            </section>
            <section className="rf-seller-banner">
              <div>
                <h2>
                  Sell furniture and decor on Roomform
                </h2>
                <p>
                  List a single pre-loved piece or your store’s collection. Add photos, prices and delivery details.
                </p>
              </div>
              <button
                className="rf-primary"
                onClick={() => navigate("seller")}
              >
                Start selling with us <ArrowUpRight size={17} />
              </button>
            </section>
            <DesignFAQ />
            <section className="home-consult">
              <div>
                <h2>
                  Ready to discuss your project?
                </h2>
                <p>
                  Connect your design, budget and product choices with the
                  people who can make it happen.
                </p>
                <button
                  className="rf-primary"
                  onClick={() => navigate("consult")}
                >
                  Plan my consultation <ArrowUpRight size={18} />
                </button>
                <small>
                  Consultation timing and any fees are confirmed separately.
                </small>
              </div>
              <div className="home-consult-image">
                <img
                  src="/images/hero.jpg"
                  alt="An inviting finished interior, shown as design inspiration"
                  loading="lazy"
                />
              </div>
            </section>
          </>
        )}
        {page === "inspiration" && (
          <main>
            <InspirationGallery full onSelect={startWith} />
            <TransformationDemos onSelect={startWith} />
            <DesignFAQ />
          </main>
        )}
        {page === "studio" && (
          <AccountGate>
            <main className="rf-studio" ref={studioRef}>
              <div className="rf-page-heading">
                <span className="rf-kicker">
                  <Sparkles size={14} /> YOUR PERSONAL DESIGN STUDIO
                </span>
                <h1>
                  Design your room
                </h1>
                <p>
                  Upload a room photo, confirm your budget, then choose the furniture and style you want to explore.
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
                      if (
                        target === ".rf-investment" ||
                        target === ".rf-settings"
                      )
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
                      {done ? (
                        <Check size={16} />
                      ) : (
                        String(i + 1).padStart(2, "0")
                      )}
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
                    <span>
                      {design ? "Your concept is ready" : "Let’s begin"}
                    </span>
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
                          <span className="budget-step">02</span> Beautiful,
                          within your budget.
                        </h3>
                        <p>
                          Confirm your budget and condition preference. Catalog
                          matching chooses in-stock references; your selected AI
                          model reimagines the room.
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
                              <option value="auto">
                                Choose products for me
                              </option>
                              <option value="manual">
                                I’ll choose products myself
                              </option>
                            </select>
                          </label>
                          <label className="consent">
                            <input
                              type="checkbox"
                              checked={budgetConfirmed}
                              onChange={(e) =>
                                setBudgetConfirmed(e.target.checked)
                              }
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
                              Verify physical fit with your designer. Inventory
                              is not reserved.
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
                          Explore ideas and prepare a brief for this space. A
                          local installation estimate is needed before budgeted
                          rendering; plumbing, structural work and landscaping
                          construction are quoted separately.
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
                              <strong>
                                Protect actual products · measured beta
                              </strong>
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
                          I agree to send my room and selected product photos to
                          this AI provider. Measured placement also shares the
                          room with the configured detection/segmentation
                          service.
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
                              placementSpec.placements.length !==
                                selected.length))
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
                              <strong>
                                {money(i.subtotal, quote.currency)}
                              </strong>
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
                          Selected product references, not verified image
                          contents. Excludes taxes and shipping; availability
                          and site costs may vary.
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
                          Request products in this design{" "}
                          <ShoppingBag size={16} />
                        </button>
                      </>
                    ) : (
                      <>
                        <p>
                          {selected.length} pieces selected. Generate your room
                          to see installation costs and a timeline.
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
        )}
        {page === "marketplace" && (
          <main className="rf-section">
            <div className="rf-page-heading">
              <span className="rf-kicker">
                THOUGHTFULLY CHOSEN. READY FOR A NEW CHAPTER.
              </span>
              <h1>
                Find your next
                <br />
                <em>favorite piece.</em>
              </h1>
              <p>
                New finds and pre-loved character. Add up to eight pieces to
                your next room.
              </p>
            </div>
            <div className="rf-market-controls">
              <input
                aria-label="Search furniture"
                placeholder="Find a sofa, lamp, or something special…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select
                aria-label="Product condition"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
              >
                <option value="all">All pieces</option>
                <option value="new">New</option>
                <option value="used">Pre-loved</option>
              </select>
              <button
                className="rf-text-button"
                onClick={findLocal}
                disabled={geoBusy}
              >
                <MapPin size={16} />
                {local ? "Show all locations" : "Near me · 50 km"}
              </button>
            </div>
            <p className="rf-subtle">
              Actual seller photography. Check every angle and confirm fit and
              delivery before ordering.
            </p>
            {productGrid(filtered)}
            {!filtered.length && (
              <p className="rf-empty-state">
                No pieces match just yet. Try another search or location.
              </p>
            )}
            <div className="rf-selection-bar">
              <span>{selected.length} pieces in your design</span>
              <button className="rf-primary" onClick={() => navigate("studio")}>
                Design with these pieces <ArrowRight size={17} />
              </button>
              <button
                className="rf-primary"
                onClick={() => setCheckoutOpen(!checkoutOpen)}
                disabled={!selected.length}
              >
                Request selected products
              </button>
            </div>
            {checkoutOpen && <Checkout assetIds={selected} />}
          </main>
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
        <footer className="atelier-footer">
          <div className="footer-top">
            <div>
              <a
                className="footer-wordmark"
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("discover");
                }}
              >
                roomform.
              </a>
              <p>
                Good spaces. Real pieces.
                <br />A place that feels like you.
              </p>
            </div>
            <div>
              <span>CREATE YOUR SPACE</span>
              <button onClick={() => navigate("studio")}>Design studio</button>
              <button onClick={() => navigate("inspiration")}>
                Inspiration gallery
              </button>
              <button onClick={() => navigate("marketplace")}>
                Shop real furniture
              </button>
              <button onClick={() => navigate("consult")}>
                Book a consultation
              </button>
            </div>
            <div>
              <span>GROW WITH ROOMFORM</span>
              <button onClick={() => navigate("seller")}>
                Sell furniture & décor
              </button>
              <button onClick={() => navigate("professionals")}>
                Local professionals
              </button>
              <button onClick={() => navigate("teams")}>
                Roomform for business
              </button>
            </div>
            <button className="footer-start" onClick={() => navigate("studio")}>
              Your next chapter
              <br />
              starts at home. <ArrowUpRight size={28} />
            </button>
          </div>
          <div className="footer-bottom">
            <span>© {new Date().getFullYear()} Roomform</span>
            <span>From inspiration to installation.</span>
            <button onClick={() => navigate("operations")}>
              Partner administration <ArrowUpRight size={12} />
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")).render(
  <WorkspaceProvider>
    <App />
  </WorkspaceProvider>,
);
