import React from "react";
import {
  ArrowUpRight,
  Layers,
  X,
  Menu,
  Users as UsersIcon,
} from "lucide-react";

export default function AppHeader({
  mobile,
  nav,
  navigate,
  page,
  setMobile,
  workspace,
}) {
  return (
    <>
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
          <button className="header-seller" onClick={() => navigate("seller")}>
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
    </>
  );
}
