import React from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Sparkles,
  ShoppingBag,
  Leaf,
} from "lucide-react";

import { Consultation } from "../Workspace";

import ExperienceHero from "../ExperienceHero";

import { DesignTools, MarketplaceStory, DesignFAQ } from "../DesignDiscovery";

import { DesignCategories, RedesignPanels } from "../AppHomeSections";
import InspirationGallery from "../CuratedInspirations";

export default function HomePage({
  assets,
  selected,
  navigate,
  productGrid,
  setInvestment,
  setCurrency,
  setBudgetConfirmed,
  setBrief,
  invalidate,
  startWith,
}) {
  return (
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
            <h2>Furniture from our sellers</h2>
          </div>
          <button
            className="rf-text-button"
            onClick={() => navigate("marketplace")}
          >
            Explore the collection <ArrowUpRight size={17} />
          </button>
        </div>
        <p className="rf-subtle">
          Discover pieces photographed by real sellers. Their original angles,
          condition and current price stay connected to the listing.
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
            Explore your space, source real products, and meet the people who
            can bring it together.
          </p>
          <small>
            One-time image packages launch with AI. Product previews and project
            planning are available now.
          </small>
        </div>
        <div>
          <strong>
            $3–$5 <span>USD / project package</span>
          </strong>
          <p>3 or 6 images · products and services priced separately</p>
          <button className="rf-primary" onClick={() => navigate("projects")}>
            Start your project <ArrowUpRight size={16} />
          </button>
          <button className="rf-text-button" onClick={() => navigate("teams")}>
            Explore business plans →
          </button>
        </div>
      </section>
      <section className="rf-seller-banner">
        <div>
          <h2>Sell furniture and decor on Roomform</h2>
          <p>
            List a single pre-loved piece or your store’s collection. Add
            photos, prices and delivery details.
          </p>
        </div>
        <button className="rf-primary" onClick={() => navigate("seller")}>
          Start selling with us <ArrowUpRight size={17} />
        </button>
      </section>
      <DesignFAQ />
      <section className="home-consult">
        <div>
          <h2>Ready to discuss your project?</h2>
          <p>
            Connect your design, budget and product choices with the people who
            can make it happen.
          </p>
          <button className="rf-primary" onClick={() => navigate("consult")}>
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
  );
}
