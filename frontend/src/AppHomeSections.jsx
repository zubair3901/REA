import React, { useEffect, useState } from "react";
import { Armchair, House, Trees, CookingPot, ArrowUpRight, Pause, Play } from "lucide-react";
import "./app-home.css";

const categories = [
  {room:"living",label:"Interior design",copy:"Rooms built around your life and real furniture.",Icon:Armchair,brief:"Redesign my interior using available seller furniture and decor, my confirmed budget and my preferred aesthetic. Preserve existing room geometry."},
  {room:"exterior",label:"Exterior design",copy:"Explore a fresh look for the outside of your home.",Icon:House,brief:"Explore exterior finishes, lighting and outdoor products within my confirmed budget. Preserve the building geometry and openings."},
  {room:"landscape",label:"Landscape design",copy:"Make more of your garden and outdoor space.",Icon:Trees,brief:"Redesign my outdoor landscape with suitable available products and my confirmed budget. Preserve access routes and existing building geometry."},
  {room:"kitchen",label:"Kitchen design",copy:"Plan finishes, lighting and a place to gather.",Icon:CookingPot,brief:"Redesign my kitchen with available furniture, lighting and decor within my confirmed budget. Preserve openings and service locations; structural work requires confirmation."},
];
const selection = (category) => ({room:category.room,style:"modern",name:category.label,brief:category.brief});
export function DesignCategories({onSelect}) {
 return <section className="app-design-section" aria-labelledby="app-design-title">
  <div className="app-section-heading"><h2 id="app-design-title">What would you like to redesign?</h2><p>Choose a space. Bring your inspiration, then set a budget that works for you.</p></div>
  <div className="app-design-grid">{categories.map(({Icon,...category})=><button className="app-design-category" key={category.room} onClick={()=>onSelect(selection(category))}><span className={"app-category-icon "+category.room}><Icon size={23}/></span><strong>{category.label}</strong><span>{category.copy}</span><ArrowUpRight className="app-category-arrow" size={19}/></button>)}</div>
 </section>;
}
export function RedesignPanels({onSelect}) {
 const [playing,setPlaying]=useState(false);
 useEffect(()=>{const media=matchMedia("(prefers-reduced-motion: reduce)");const update=()=>setPlaying(!media.matches);update();media.addEventListener("change",update);return()=>media.removeEventListener("change",update);},[]);
 return <section className="app-redesign-section" aria-labelledby="app-redesign-title">
  <div className="app-section-heading"><h2 id="app-redesign-title">From an idea to your own space</h2><p>Start with a look you love. Plan around real products, your budget and local availability.</p></div>
  <div className="app-redesign-panels">
   <article className="app-redesign-panel"><div className="app-redesign-media"><img src="/inspiration/photos/156466242.jpg" alt="Kitchen showroom with fitted cabinets and work surfaces" loading="lazy" width="800" height="600"/><span className="app-media-label">Kitchen inspiration</span></div><div className="app-redesign-copy"><h3>Make room for a better kitchen</h3><p>Explore a style, upload your kitchen and set your investment. Review product options before deciding what to bring home.</p><a href="?page=studio" onClick={e=>{e.preventDefault();onSelect(selection(categories[3]));}}>Explore kitchen redesign <ArrowUpRight size={17}/></a><details className="app-media-credit"><summary>Photo credit &amp; media details</summary><p>Reference image from the existing inspiration collection. A kitchen video has not been supplied yet. This image is not a product listing.</p><a href="https://commons.wikimedia.org/wiki/File:IKEA_store,_IKEA_kitchen,_Interior_design,_Rostov-on-Don,_Russia.jpg" target="_blank" rel="noreferrer">Vyacheslav Argenberg · CC BY 4.0</a></details></div></article>
   <article className="app-redesign-panel"><div className="app-redesign-media"><img src={playing?"/demos/living.gif":"/demos/living-poster.jpg"} alt="Illustrated workers assembling and styling a living room" loading="lazy" width="560" height="560"/><span className="app-media-label">Illustrative renovation montage</span><button type="button" className="app-media-play" aria-label={(playing?"Pause":"Play")+" interior renovation montage"} aria-pressed={playing} onClick={()=>setPlaying(!playing)}>{playing?<Pause size={18}/>:<Play size={18}/>}</button></div><div className="app-redesign-copy"><h3>A room that feels like you</h3><p>Find furniture and decor from our sellers, compare your options and keep every selected item connected to your design.</p><a href="?page=studio" onClick={e=>{e.preventDefault();onSelect(selection(categories[0]));}}>Explore interior redesign <ArrowUpRight size={17}/></a><small>Illustrative animation, not footage of a completed customer project.</small></div></article>
  </div>
 </section>;
}
