import React, { useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Camera,
  Check,
  MoveHorizontal,
  Sparkles,
  Leaf,
  ShoppingBag,
} from "lucide-react";
import "./photography.css";

export default function ExperienceHero({ onStart, onSellers }) {
  const [position, setPosition] = useState(35);
  const [mode, setMode] = useState("interior");
  const services = [
    ["interior", "A complete refresh"],
    ["furniture", "Furniture that fits"],
    ["walls", "A new mood"],
  ];
  return (
    <section className="atelier-hero">
      <div className="hero-intro">
        <div>
          <span className="rf-kicker">
            <span className="live-dot" /> A NEW WAY TO FEEL AT HOME
          </span>
          <h1>
            A space you love.
            <br />
            <em>A way to make it real.</em>
          </h1>
        </div>
        <div className="hero-intro-right">
          <p>
            Reimagine your room. Discover real furniture.
            <br className="desktop-break" /> Bring it together, beautifully
            within budget.
          </p>
          <button
            className="rf-primary hero-start"
            onClick={() => onStart({ budget: 2500, service: mode })}
          >
            Redesign my space <ArrowUpRight size={20} />
          </button>
          <span className="hero-microcopy">
            Your room photo. Your budget. Your possibilities.
          </span>
        </div>
      </div>
      <div className="hero-visual-wrap">
        <div
          className="hero-service-tabs"
          role="group"
          aria-label="Choose a redesign direction"
        >
          {services.map(([id, label]) => (
            <button
              key={id}
              aria-pressed={mode === id}
              onClick={() => setMode(id)}
            >
              {id === "interior" ? (
                <Sparkles size={15} />
              ) : id === "furniture" ? (
                <ShoppingBag size={15} />
              ) : (
                <Leaf size={15} />
              )}
              <span>{label}</span>
            </button>
          ))}
        </div>
        <div
          className="hero-comparison"
          style={{ "--comparison-position": position + "%" }}
        >
          <img
            className="comparison-after"
            src="/images/living.jpg"
            alt="Furnished living room inspiration with leather sofa, natural wood and warm daylight"
            fetchPriority="high"
          />
          <div className="comparison-before">
            <img
              src="/images/living-before.png"
              alt="Illustrative empty version of the same living room"
              fetchPriority="high"
            />
          </div>
          <span className="comparison-label before">The starting point</span>
          <span className="comparison-label after">
            The possibility <Sparkles size={13} />
          </span>
          <div className="comparison-line">
            <span>
              <MoveHorizontal size={22} />
            </span>
          </div>
          <input
            className="hero-comparison-input"
            aria-label="Explore the room before and after"
            aria-valuetext={`${position}% starting room visible`}
            type="range"
            min="0"
            max="100"
            value={position}
            onChange={(e) => setPosition(Number(e.target.value))}
          />
          <div className="comparison-caption">
            <span>ROOM TO REIMAGINE</span>
            <strong>Same room. A different feeling.</strong>
            <small>
              Drag to explore <MoveHorizontal size={13} />
            </small>
          </div>
        </div>
        <div className="hero-image-meta">
          <span>
            <Camera size={13} /> Illustrative comparison · AI-edited empty room
            and inspiration photograph
          </span>
          <span>Real rooms. Thoughtful possibilities.</span>
        </div>
      </div>
      <div className="hero-bottom">
        <div className="hero-values">
          <span>
            <Check size={15} /> Your budget comes first
          </span>
          <span>
            <Check size={15} /> New & pre-loved pieces
          </span>
          <span>
            <Check size={15} /> Connected to real sellers
          </span>
        </div>
        <button className="rf-text-button" onClick={onSellers}>
          Have a piece worth discovering? <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}
