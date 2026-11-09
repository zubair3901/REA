import React from "react";
import { Home, FolderHeart, Images, ShoppingBag, Users, WandSparkles, Armchair, House, Trees, CookingPot, ArrowUpRight } from "lucide-react";
import "./app-navigation.css";

const destinations = [
  ["discover", Home, "Home"],
  ["projects", FolderHeart, "My projects"],
  ["inspiration", Images, "Inspiration"],
  ["marketplace", ShoppingBag, "Shop furniture"],
  ["professionals", Users, "Professionals"],
];
const mobileDestinations = [
  ["discover", Home, "Home"],
  ["inspiration", Images, "Ideas"],
  ["studio", WandSparkles, "Design"],
  ["marketplace", ShoppingBag, "Shop"],
  ["projects", FolderHeart, "Projects"],
];
const categories = [
  ["living", Armchair, "Interior design"],
  ["exterior", House, "Exterior design"],
  ["landscape", Trees, "Landscape design"],
  ["kitchen", CookingPot, "Kitchen design"],
];
export default function AppNavigation({ page, navigate, onDesign }) {
  return <>
    <aside className="app-navigation-rail" aria-label="Roomform workspace">
      <button className="app-rail-brand" onClick={() => navigate("discover")} aria-label="Roomform home"><House size={22}/><span>roomform<span>.</span></span></button>
      <nav className="app-rail-pages" aria-label="Workspace navigation">
        {destinations.map(([id, Icon, label]) => <button key={id} aria-current={page === id ? "page" : undefined} onClick={() => navigate(id)}><Icon size={19}/><span>{label}</span></button>)}
      </nav>
      <div className="app-rail-designs">
        <p>Design your space</p>
        <nav aria-label="Design categories">{categories.map(([room, Icon, label]) => <button key={room} onClick={() => onDesign ? onDesign({ room, style: "modern", brief: "Design my " + room + " using my budget and real seller inventory." }) : navigate("studio")}><Icon size={18}/><span>{label}</span><ArrowUpRight size={14}/></button>)}</nav>
      </div>
      <div className="app-rail-bottom"><p>Real pieces. Your budget.<br/>A home you can bring to life.</p><button onClick={() => navigate("partners")}>Sell your furniture <ArrowUpRight size={16}/></button></div>
    </aside>
    <nav className="app-mobile-tabs" aria-label="Mobile app navigation">
      {mobileDestinations.map(([id, Icon, label]) => <button key={id} className={id === "studio" ? "app-mobile-design" : undefined} aria-current={page === id ? "page" : undefined} onClick={() => navigate(id)}><Icon size={21}/><span>{label}</span></button>)}
    </nav>
  </>;
}
