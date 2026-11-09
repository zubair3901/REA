import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, ArrowUpRight, Search, ImageOff, RefreshCw } from "lucide-react";
import "./curated-inspirations.css";

const categories = [["all","All spaces"],["living","Living room"],["bedroom","Bedroom"],["kitchen","Kitchen"],["office","Office"],["bathroom","Bathroom"],["restaurant","Restaurants"],["garden","Garden"],["landscape","Landscape"],["dining","Dining room"],["exterior","Exterior"]];
function selectedCategory() {
  const value = new URL(location.href).searchParams.get("category");
  return categories.some(([id]) => id === value) ? value : "all";
}
function ImageCard({ item, onSelect }) {
  const [failed,setFailed] = useState(false);
  return <article className="curated-card">
    <div className="curated-photo" style={{aspectRatio: `${item.width || 4} / ${item.height || 3}`}}>
      {failed ? <span className="curated-image-error"><ImageOff size={24}/> Image unavailable</span> : <img src={item.image} alt={item.description || item.name} width={item.width} height={item.height} loading="lazy" decoding="async" onError={()=>setFailed(true)}/>}
      <span className="curated-room-label">{categories.find(([id])=>id===item.category)?.[1] || "Interior"}</span>
    </div>
    <div className="curated-card-copy"><h3>{item.name}</h3><p>{item.description}</p>
      <button className="curated-design" onClick={()=>onSelect({room:item.category,style:["minimalist","modern","mid-century","scandinavian"].includes(item.style)?item.style:"modern",name:item.name,brief:(`Create a ${item.category} design inspired by ${item.name}. ${item.description} Preserve my uploaded space's geometry and work within my budget using real seller inventory. This reference is inspiration, not a stocked product list.`).slice(0,1200)})}>Design this <ArrowUpRight size={17}/></button>
    </div>
  </article>;
}
export default function CuratedInspirations({onSelect,onExplore,full=false}) {
  const [items,setItems]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState(""),[retry,setRetry]=useState(0);
  const [filter,setFilter]=useState(selectedCategory),[search,setSearch]=useState(""),[limit,setLimit]=useState(24);
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setError("");
    fetch("/inspiration/curated.json",{signal:controller.signal}).then(r=>{if(!r.ok)throw Error("Could not load the inspiration collection.");return r.json();}).then(data=>{if(!Array.isArray(data))throw Error("The collection format is unavailable.");setItems(data);}).catch(e=>{if(e.name!=="AbortError")setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[retry]);
  useEffect(()=>{const pop=()=>{setFilter(selectedCategory());setLimit(24);};window.addEventListener("popstate",pop);return()=>window.removeEventListener("popstate",pop);},[]);
  const counts=useMemo(()=>items.reduce((all,item)=>({...all,[item.category]:(all[item.category]||0)+1}),{}),[items]);
  const filtered=items.filter(item=>(filter==="all"||item.category===filter)&&(!search.trim()||(item.name+" "+item.description).toLowerCase().includes(search.trim().toLowerCase())));
  const previewItems=useMemo(()=>{
    const groups=categories.filter(([id])=>id!=="all").map(([id])=>items.filter(item=>item.category===id));
    const mixed=[];
    for(let index=0;mixed.length<12&&groups.some(group=>index<group.length);index++) {
      for(const group of groups) {if(group[index])mixed.push(group[index]);if(mixed.length===12)break;}
    }
    return mixed;
  },[items]);
  const visible=full?filtered.slice(0,limit):previewItems;
  function choose(id){setFilter(id);setLimit(24);const url=new URL(location.href);if(id==="all")url.searchParams.delete("category");else url.searchParams.set("category",id);history.replaceState({},"",url);}
  return <section className={"curated-inspirations "+(full?"curated-full":"curated-preview")} aria-labelledby={full?"curated-library-title":"curated-preview-title"}>
    <div className="curated-heading"><div>{full?<h1 id="curated-library-title">Find a look you love</h1>:<h2 id="curated-preview-title">A little inspiration.<br/><em>A space that's yours.</em></h2>}<p>{full?"Browse the collection by room, find your direction and make it work for your home.":"Explore warm, lived-in spaces. Choose a look, set your budget and start with your own room."}</p></div><span className="curated-collection-note">{!loading && !error && `${items.length} design references`}</span></div>
    {full&&<><div className="curated-filters" role="group" aria-label="Inspiration categories">{categories.map(([id,label])=><button key={id} aria-pressed={filter===id} onClick={()=>choose(id)}>{label}<span>{id==="all"?items.length:counts[id]||0}</span></button>)}</div><div className="curated-toolbar"><p role="status">{loading?"Opening the collection…":`${filtered.length} ${filter==="all"?"design":categories.find(([id])=>id===filter)?.[1].toLowerCase()} references`}</p><label className="curated-search"><Search size={18}/><input aria-label="Search inspiration" placeholder="Search styles, colors or rooms" value={search} onChange={e=>{setSearch(e.target.value);setLimit(24);}}/></label></div></>}
    {error&&<div className="curated-empty" role="alert"><ImageOff size={28}/><h3>The collection couldn’t load</h3><p>{error}</p><button className="rf-text-button" onClick={()=>setRetry(v=>v+1)}><RefreshCw size={16}/> Try again</button></div>}
    {!error&&loading&&<p role="status" className="curated-loading">Loading inspiration images…</p>}
    {!loading&&!error&&!visible.length&&<div className="curated-empty"><ImageOff size={28}/><h3>{search?"No matching inspiration":`No ${categories.find(([id])=>id===filter)?.[1].toLowerCase()} images in this collection yet`}</h3><p>{search?"Try a different style, color or room name.":"Explore another space while we build this part of the collection."}</p><button className="rf-text-button" onClick={()=>{choose("all");setSearch("");}}>Browse all spaces <ArrowRight size={16}/></button></div>}
    <div className="curated-masonry" aria-busy={loading}>{visible.map(item=><ImageCard key={item.id} item={item} onSelect={onSelect}/>)}</div>
    {full&&filtered.length>limit&&<div className="curated-more"><button className="rf-primary" onClick={()=>setLimit(value=>value+24)}>Show more designs <ArrowRight size={17}/></button><span>Showing {visible.length} of {filtered.length}</span></div>}
    {!full&&<div className="curated-more"><a href="?page=inspiration" className="rf-primary" onClick={e=>{if(onExplore){e.preventDefault();onExplore();}}}>Load more Inspirations <ArrowRight size={17}/></a><span>Find your style, room by room.</span></div>}
    <p className="curated-reference-note">Provided inspiration references. Pictured items are not confirmed marketplace inventory. “Design this” starts your own room and budget brief.</p>
  </section>;
}
