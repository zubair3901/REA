import React, { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Armchair,
  BedDouble,
  BriefcaseBusiness,
  Sparkles,
  Wallet,
  Camera,
  Pause,
  Play,
  Check,
  MapPin,
  ShoppingBag,
} from "lucide-react";

export const inspirationRooms = [
  {
    id: "sunlit",
    name: "A little more breathing room",
    tag: "Warm minimalism",
    style: "minimalist",
    room: "living",
    image: "living",
    brief:
      "Create a warm minimalist living room with natural textures, calm neutral walls and an uncluttered layout. Preserve the room architecture.",
  },
  {
    id: "retreat",
    name: "An everyday escape",
    tag: "Warm contemporary",
    style: "modern",
    room: "bedroom",
    image: "bedroom",
    brief:
      "Create a restful bedroom with warm wood, layered textiles and soft lighting. Preserve the existing windows and room geometry.",
  },
  {
    id: "gather",
    name: "Made for good company",
    tag: "Soft Scandinavian",
    style: "scandinavian",
    room: "living",
    image: "dining",
    brief:
      "Create an inviting Scandinavian living space with warm wood, green accents and gentle lighting, using real catalog products.",
  },
  {
    id: "light",
    name: "Light, space and a fresh start",
    tag: "Quiet modern",
    style: "modern",
    room: "living",
    image: "hero",
    brief:
      "Create an airy modern living room with a warm neutral palette, sculptural furniture and natural light. Preserve the architecture.",
  },
  {
    id: "focus",
    name: "A calmer kind of workday",
    tag: "Modern workspace",
    style: "modern",
    room: "office",
    image: "office",
    brief:
      "Create a comfortable home office with a clear desk, supportive seating and warm lighting, while preserving room architecture.",
  },
  {
    id: "rest",
    name: "Room to switch off",
    tag: "Soft minimalism",
    style: "minimalist",
    room: "bedroom",
    image: "bedroom-light",
    brief:
      "Create a calm minimalist bedroom with soft neutral textiles, warm wood and layered lighting, preserving the room layout.",
  },
];
export function RoomCategories({ onSelect }) {
  return (
    <section className="discovery-section room-discovery">
      <div className="discovery-heading">
        <div>
          <h2>
            Where would you like to start?
          </h2>
        </div>
        <p>
          Choose a room to start your design.
        </p>
      </div>
      <div className="room-category-grid">
        {[
          [
            "living",
            Armchair,
            "Living room",
            "A place to come together.",
            "living",
          ],
          [
            "bedroom",
            BedDouble,
            "Bedroom",
            "A little more sanctuary.",
            "bedroom-light",
          ],
          [
            "office",
            BriefcaseBusiness,
            "Home office",
            "Make room for good ideas.",
            "office",
          ],
        ].map(([room, Icon, title, copy, image]) => (
          <button
            key={room}
            className="room-category-card"
            onClick={() =>
              onSelect(inspirationRooms.find((i) => i.room === room))
            }
          >
            <img
              src={"/images/" + image + ".jpg"}
              alt={title + " design inspiration"}
              loading="lazy"
            />
            <div>
              <span>
                <Icon size={18} />
                {title}
              </span>
              <small>{copy}</small>
              <ArrowUpRight size={23} />
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
function Transformation({ scene, title, description, onSelect }) {
  const [playing, setPlaying] = useState(false),
    [visible, setVisible] = useState(false),
    [reduced, setReduced] = useState(false);
  const host = useRef(null);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      setReduced(media.matches);
      setPlaying(!media.matches);
    };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin: "100px" },
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, []);
  const active = playing && visible;
  return (
    <article className="transformation-card" ref={host}>
      <div className="transformation-media worker-timelapse">
        <img
          src={
            active
              ? "/demos/" + scene + ".gif"
              : "/demos/" + scene + "-poster.jpg"
          }
          alt={title + " — AI-illustrated staged workers renovation montage"}
          loading="lazy"
          width="560"
          height="560"
        />
        <span className="demo-badge">
          <Sparkles size={12} /> WORKERS TIMELAPSE
        </span>
        <button
          className="demo-play"
          aria-label={(playing ? "Pause" : "Play") + " " + title + " animation"}
          aria-pressed={playing}
          onClick={() => setPlaying(!playing)}
        >
          {playing ? <Pause size={15} /> : <Play size={15} />}
        </button>
        <div className="demo-corner">
          <span>PREPARE · INSTALL · STYLE</span>
          <ArrowRight size={16} />
          <span>THE FINISHED ROOM</span>
        </div>
      </div>
      <div className="transformation-copy">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <button className="rf-text-button" onClick={onSelect}>
          Try this room style <ArrowUpRight size={16} />
        </button>
      </div>
      {reduced && (
        <small className="demo-reduced">
          Motion is paused to match your device preference.
        </small>
      )}
    </article>
  );
}
export function TransformationDemos({ onSelect }) {
  return (
    <section className="transformation-section">
      <div className="discovery-heading">
        <div>
          <h2>
            See how a room comes together
          </h2>
        </div>
        <p>
          Watch these illustrated examples of a living room and bedroom refresh.
        </p>
      </div>
      <div className="transformation-grid">
        <Transformation
          scene="living"
          title="From empty to inviting"
          description="A living room refreshed with seating, lighting and finishing touches."
          onSelect={() => onSelect(inspirationRooms[0])}
        />
        <Transformation
          scene="bedroom"
          title="From a room to a retreat"
          description="Layered lighting and natural materials, brought into balance."
          onSelect={() => onSelect(inspirationRooms[1])}
        />
      </div>
      <p className="demo-disclosure">
        <Camera size={14} /> AI-illustrated worker montage: staged preparation,
        furniture installation and styling. Not continuous real-world footage, a
        construction schedule or purchasable product combinations.
      </p>
    </section>
  );
}
export const inspirationCategories = [
  ["living", "Living room"],
  ["bedroom", "Bedroom"],
  ["kitchen", "Kitchen"],
  ["bathroom", "Bathroom"],
  ["restaurant", "Restaurant"],
  ["garden", "Garden"],
  ["exterior", "Exteriors"],
  ["landscape", "Landscape"],
  ["office", "Office"],
  ["dining", "Dining room"],
];
export function InspirationGallery({ onSelect, full = false, onExplore }) {
  const [filter, setFilter] = useState(() => {
      const value = new URLSearchParams(location.search).get("category");
      return inspirationCategories.some((c) => c[0] === value)
        ? value
        : "living";
    }),
    [items, setItems] = useState([]),
    [counts, setCounts] = useState({}),
    [page, setPage] = useState(1),
    [search, setSearch] = useState(""),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const cache = useRef({});
  const host = useRef(null);
  const pageSize = full ? 24 : 6;
  useEffect(() => {
    let valid = true;
    fetch("/inspiration/index.json")
      .then((r) => {
        if (!r.ok) throw Error();
        return r.json();
      })
      .then((d) => {
        if (valid)
          setCounts(
            Object.fromEntries(d.categories.map((c) => [c.id, c.count])),
          );
      })
      .catch(() => {});
    return () => {
      valid = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setPage(1);
    setSearch("");
    setError("");
    setLoading(true);
    setItems([]);
    const apply = (d) => {
      setItems(d);
      setLoading(false);
    };
    if (cache.current[filter]) {
      apply(cache.current[filter]);
      return () => controller.abort();
    }
    fetch("/inspiration/" + filter + ".json", { signal: controller.signal })
      .then((r) => {
        if (!r.ok)
          throw Error(
            "This inspiration collection could not load. Please try again.",
          );
        return r.json();
      })
      .then((d) => {
        cache.current[filter] = d;
        apply(d);
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [filter]);
  const matching = items.filter((i) =>
    (i.name + " " + i.description).toLowerCase().includes(search.toLowerCase()),
  );
  const pages = Math.max(1, Math.ceil(matching.length / pageSize));
  const visible = matching.slice((page - 1) * pageSize, page * pageSize);
  function changePage(next) {
    setPage(next);
    host.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }
  return (
    <section
      ref={host}
      className={
        "discovery-section inspiration-discovery " + (full ? "full" : "")
      }
    >
      <div className="discovery-heading">
        <div>
          {full ? (
            <h1>
              Find a look you love
            </h1>
          ) : (
            <h2>
              Ideas for your next room
            </h2>
          )}
        </div>
        {full && (
          <p>
            Browse by room, then choose a reference to guide your design.
          </p>
        )}
      </div>
      <div
        className="discovery-filters inspiration-category-tabs"
        role="group"
        aria-label="Inspiration categories"
      >
        {inspirationCategories.map(([id, label]) => (
          <button
            key={id}
            aria-pressed={filter === id}
            onClick={() => {
              setFilter(id);
              const url = new URL(location.href);
              url.searchParams.set("category", id);
              history.replaceState({}, "", url);
            }}
          >
            {label}
            {counts[id] !== undefined && <span>{counts[id]}</span>}
          </button>
        ))}
      </div>
      <div className="inspiration-library-toolbar">
        <p role="status">
          {loading
            ? "Opening the collection…"
            : matching.length +
              " " +
              (inspirationCategories.find((c) => c[0] === filter)?.[1] || "") +
              " references"}
          {!loading && matching.length > 0 && (
            <span>
              {" "}
              · Showing {(page - 1) * pageSize + 1}–
              {Math.min(page * pageSize, matching.length)}
            </span>
          )}
        </p>
        {full && (
          <input
            aria-label="Search this inspiration category"
            placeholder="Search this collection…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        )}
      </div>
      {error && (
        <p className="ws-notice error" role="alert">
          {error}
        </p>
      )}
      {!loading && !error && !matching.length && (
        <p className="ws-notice">
          No references match this search. Try another term.
        </p>
      )}
      <div className="inspiration-gallery" aria-busy={loading}>
        {visible.map((item) => (
          <article key={item.id} className="inspiration-tile">
            <InspirationPhoto item={item} />
            <span className="inspiration-meta">
              {inspirationCategories.find((c) => c[0] === item.category)?.[1]}
              <span>Design reference</span>
            </span>
            <h3 title={item.name}>{item.name}</h3>
            <p className="inspiration-description">{item.description}</p>
            <button
              className="rf-primary inspiration-design"
              onClick={() =>
                onSelect({
                  room: item.category,
                  style: "modern",
                  name: item.name,
                  brief: (
                    "Explore a " +
                    (inspirationCategories.find(
                      (c) => c[0] === item.category,
                    )?.[1] || item.category) +
                    " design inspired by this photographic reference: " +
                    item.name +
                    ". " +
                    item.description +
                    ". Preserve my uploaded space’s geometry, use my budget and real seller products. The reference is inspiration, not merchant inventory."
                  ).slice(0, 1200),
                })
              }
            >
              Design this <ArrowUpRight size={16} />
            </button>
            <details className="inspiration-credit">
              <summary>Photo credit & license</summary>
              <p>
                {item.creator} ·{" "}
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Wikimedia Commons source
                </a>{" "}
                ·{" "}
                <a
                  href={item.license_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {item.license}
                </a>
              </p>
            </details>
          </article>
        ))}
      </div>
      {!full && <div className="inspiration-more"><button className="rf-primary" onClick={onExplore}>Load more Inspirations <ArrowUpRight size={17} /></button></div>}
      {full && pages > 1 && (
        <nav className="inspiration-pagination" aria-label="Inspiration pages">
          <button
            className="rf-text-button"
            disabled={page <= 1}
            onClick={() => changePage(page - 1)}
          >
            Previous
          </button>
          <span>
            Page {page} of {pages}
          </span>
          <button
            className="rf-text-button"
            disabled={page >= pages}
            onClick={() => changePage(page + 1)}
          >
            Next
          </button>
        </nav>
      )}
      <p className="inspiration-footnote">
        Reference imagery for inspiration, with source credits and licenses
        below each image. “Design this” begins your own design brief; pictured
        products may not be available in our marketplace.
      </p>
    </section>
  );
}
function InspirationPhoto({ item }) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="inspiration-photo">
      {failed ? (
        <span className="inspiration-unavailable">
          <Camera size={24} />
          Photograph unavailable
          <br />
          See the original source below.
        </span>
      ) : (
        <img
          src={item.image_url}
          alt={item.name}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
        />
      )}
    </div>
  );
}
export function DesignTools({ navigate }) {
  return (
    <section className="discovery-section tool-discovery">
      <div className="discovery-heading">
        <div>
          <h2>
            Everything for your room project
          </h2>
        </div>
        <p>
          Design a room, find the furniture and connect with local professionals.
        </p>
      </div>
      <div className="tool-grid">
        {[
          [
            Sparkles,
            "Reimagine your room",
            "Upload a room photo, choose a style and review your design options.",
            "studio",
            "Open the studio",
          ],
          [
            ShoppingBag,
            "Find the real pieces",
            "Explore actual seller photos, current stock and new or pre-loved finds.",
            "marketplace",
            "Shop the collection",
          ],
          [
            Wallet,
            "Plan around your budget",
            "Set your investment ceiling and see item costs, labor estimates and timelines.",
            "studio",
            "Plan my space",
          ],
          [
            MapPin,
            "Meet the right people",
            "Find local professionals and request a consultation for your saved project.",
            "professionals",
            "Find an expert",
          ],
        ].map(([Icon, title, copy, page, cta], i) => (
          <button key={title} onClick={() => navigate(page)}>
            <span className="tool-number">0{i + 1}</span>
            <Icon size={25} />
            <h3>{title}</h3>
            <p>{copy}</p>
            <span className="tool-cta">
              {cta}
              <ArrowUpRight size={16} />
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
export function MarketplaceStory({ navigate }) {
  return (
    <section className="marketplace-story">
      <div className="marketplace-story-image">
        <img
          src="/images/dining.jpg"
          alt="A considered interior with warm wood furniture and green upholstered chairs"
          loading="lazy"
        />
        <span>
          REAL PIECES.
          <br />
          <em>Real possibilities.</em>
        </span>
      </div>
      <div>
        <h2>
          Real furniture. Clear product details.
        </h2>
        <p>
          Compare original seller photographs, prices and delivery details before choosing pieces for your room.
        </p>
        <ul>
          <li>
            <Check size={17} />
            <span>Original seller photography, not invented inventory.</span>
          </li>
          <li>
            <Check size={17} />
            <span>New and pre-loved pieces, with condition and stock.</span>
          </li>
          <li>
            <Check size={17} />
            <span>Delivery details and consultation, all in one place.</span>
          </li>
        </ul>
        <button className="rf-primary" onClick={() => navigate("marketplace")}>
          Explore real furniture <ArrowUpRight size={18} />
        </button>
        <button className="rf-text-button" onClick={() => navigate("partners")}>
          List your furniture or decor <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}
export function DesignFAQ() {
  const questions = [
    [
      "How do I start designing my room?",
      "Create a Roomform account and a project, upload your room photograph, then set your budget and preference for new or pre-loved furniture. Choose real product references and an available design engine.",
    ],
    [
      "Can I buy the furniture I see?",
      "Selected seller listings stay linked to your project with original photos, prices, stock and delivery details. AI can change how a referenced item looks, so compare it with the original before making an order request.",
    ],
    [
      "Do I need a monthly subscription?",
      "You can explore the collection and plan a project without a monthly subscription. One-time AI packages are planned; sales remain paused until AI delivery is tested. Products, labor, delivery and consultations are priced separately.",
    ],
    [
      "Can I sell just one pre-loved piece?",
      "Yes. Individual sellers and furniture or decor merchants can create accounts. Approved sellers upload real product photographs, disclose condition, and set price, stock, dimensions and delivery coverage.",
    ],
    [
      "Are the animations real customer results?",
      "No. The worker animations are AI-illustrated staged installation montages, not real contractor recordings or a reliable construction schedule. Your room visualization is generated separately from your photo and selected product references.",
    ],
    [
      "Does Roomform provide floor plans or a 3D walkthrough?",
      "Those tools are not part of the current release. The current focus is room redesign, real furniture and decor, budgets, seller onboarding and consultation requests.",
    ],
  ];
  return (
    <section className="discovery-section design-faq">
      <div>
        <h2>
          Questions before you start?
        </h2>
        <p>Here’s how designing, shopping and selling work.</p>
      </div>
      <div>
        {questions.map(([q, a]) => (
          <details key={q}>
            <summary>
              {q}
              <span>+</span>
            </summary>
            <p>{a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
