import React from "react";
import { ArrowUpRight } from "lucide-react";

export default function AppFooter({ navigate }) {
  return (
    <>
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
    </>
  );
}
