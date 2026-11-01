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
          <span className="rf-kicker">
            A SMALL CHANGE. A WHOLE NEW FEELING.
          </span>
          <h2>
            Which space is
            <br />
            <em>on your mind?</em>
          </h2>
        </div>
        <p>
          Start where you live, work or unwind.
          <br />
          We’ll help you explore the possibilities.
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
      <div className="transformation-media">
        <img
          src={
            active
              ? "/demos/" + scene + ".gif"
              : "/images/" +
                (scene === "living" ? "living" : "bedroom") +
                ".jpg"
          }
          alt={title + " — illustrative empty-to-furnished room transformation"}
          loading="lazy"
          width="640"
          height="426"
        />
        <span className="demo-badge">
          <Sparkles size={12} /> DESIGN IN MOTION
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
          <span>THE SPACE YOU HAVE</span>
          <ArrowRight size={16} />
          <span>THE SPACE YOU IMAGINE</span>
        </div>
      </div>
      <div className="transformation-copy">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <button className="rf-text-button" onClick={onSelect}>
          Try this direction <ArrowUpRight size={16} />
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
          <span className="rf-kicker">A LITTLE VISION GOES A LONG WAY</span>
          <h2>
            See the room.
            <br />
            <em>Then see the possibility.</em>
          </h2>
        </div>
        <p>
          Empty corners become everyday favorites.
          <br />
          Watch a space find its next chapter.
        </p>
      </div>
      <div className="transformation-grid">
        <Transformation
          scene="living"
          title="From empty to inviting"
          description="Warm textures. Thoughtful furniture. A place that feels like you."
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
        <Camera size={14} /> Illustrative animations made from inspiration
        photos and AI-edited empty rooms. Not live customer results or
        purchasable product combinations.
      </p>
    </section>
  );
}
export function InspirationGallery({ onSelect, full = false, onExplore }) {
  const [filter, setFilter] = useState("all");
  const items = inspirationRooms.filter(
    (i) => filter === "all" || i.room === filter,
  );
  return (
    <section
      className={
        "discovery-section inspiration-discovery " + (full ? "full" : "")
      }
    >
      <div className="discovery-heading">
        <div>
          <span className="rf-kicker">THE INSPIRATION EDIT</span>
          {full ? (
            <h1>
              Find a feeling.
              <br />
              <em>Make room for it.</em>
            </h1>
          ) : (
            <h2>
              Good spaces begin
              <br />
              <em>with a little inspiration.</em>
            </h2>
          )}
        </div>
        {!full ? (
          <button className="rf-text-button" onClick={onExplore}>
            Explore all inspiration <ArrowUpRight size={17} />
          </button>
        ) : (
          <p>
            Choose a room that speaks to you.
            <br />
            Take the direction into your own space.
          </p>
        )}
      </div>
      <div
        className="discovery-filters"
        role="group"
        aria-label="Filter inspiration by room"
      >
        {[
          ["all", "All spaces"],
          ["living", "Living rooms"],
          ["bedroom", "Bedrooms"],
          ["office", "Home offices"],
        ].map(([id, label]) => (
          <button
            key={id}
            aria-pressed={filter === id}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="inspiration-gallery">
        {items.map((item) => (
          <button
            key={item.id}
            className="inspiration-tile"
            onClick={() => onSelect(item)}
          >
            <div>
              <img
                src={"/images/" + item.image + ".jpg"}
                alt={item.name + " · interior inspiration"}
                loading="lazy"
              />
              <span className="inspiration-use">
                Design my room like this <ArrowUpRight size={17} />
              </span>
            </div>
            <span className="inspiration-meta">
              {item.tag}
              <span>
                {item.room === "office"
                  ? "Home office"
                  : item.room === "bedroom"
                    ? "Bedroom"
                    : "Living space"}
              </span>
            </span>
            <h3>{item.name}</h3>
          </button>
        ))}
      </div>
      <p className="inspiration-footnote">
        Inspiration photography · the direction you choose prefills your design
        brief, not your actual room.
      </p>
    </section>
  );
}
export function DesignTools({ navigate }) {
  return (
    <section className="discovery-section tool-discovery">
      <div className="discovery-heading">
        <div>
          <span className="rf-kicker">MORE THAN A PRETTY PICTURE</span>
          <h2>
            A clear path from
            <br />
            <em>inspiration to installation.</em>
          </h2>
        </div>
        <p>
          Your ideas, your budget, real products
          <br />
          and the people who bring it together.
        </p>
      </div>
      <div className="tool-grid">
        {[
          [
            Sparkles,
            "Reimagine your room",
            "Upload a photo and explore a new direction with your chosen design engine.",
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
        <span className="rf-kicker">THE DIFFERENCE IS IN THE DETAILS</span>
        <h2>
          Fall in love with a room.
          <br />
          <em>Find the pieces for it.</em>
        </h2>
        <p>
          A beautiful concept is just the beginning. Keep real products, real
          prices and local availability connected to your project.
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
          Have something beautiful to sell? <ArrowRight size={16} />
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
      "No. The homepage demonstrations use inspiration photography and AI-edited empty rooms. Your saved room visualization is generated separately from the photo and real product references you supply.",
    ],
    [
      "Does Roomform provide floor plans or a 3D walkthrough?",
      "Those tools are not part of the current release. The current focus is room redesign, real furniture and decor, budgets, seller onboarding and consultation requests.",
    ],
  ];
  return (
    <section className="discovery-section design-faq">
      <div>
        <span className="rf-kicker">A FEW THINGS WORTH KNOWING</span>
        <h2>
          A little clarity.
          <br />
          <em>More confidence.</em>
        </h2>
        <p>Good design starts with good questions.</p>
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
