import React from "react";
export const styles=['Minimalist','Industrial','Scandinavian','Bohemian','Traditional','Mid-century','Modern','Japandi'];
export const groups={
'Seating':['Sofa','Sectional','Accent chair','Recliner','Loveseat','Chaise lounge','Ottoman','Bench','Dining chair','Barstool','Office chair'],
'Surfaces & tables':['Dining table','Coffee table','Side table','Console table','Nightstand','Writing desk','Executive desk','Standing desk','Vanity table'],
'Storage & display':['Bookcase','Dresser','Chest of drawers','Wardrobe','Sideboard','Credenza','TV stand','Pantry cabinet','Display cabinet'],
'Beds & headboards':['Bed','Platform bed','Canopy bed','Panel bed','Upholstered bed','Headboard','Bunk bed','Daybed','Trundle'],
'Outdoor & patio':['Outdoor sofa','Outdoor chaise lounge','Outdoor dining set','Adirondack chair','Hammock','Bistro table'],
'Lighting':['Table lamp','Floor lamp','Chandelier','Pendant light','Wall sconce','Flush mount','Task light'],
'Textiles & linens':['Rug','Runner rug','Throw pillow','Throw blanket','Curtain','Bedding','Table linen'],
'Wall decor & art':['Art','Canvas painting','Wall sculpture','Tapestry','Clock','Floating shelf','Mirror'],
'Tabletop & accents':['Vase','Decorative bowl','Tray','Sculpture','Candleholder','Bookend','Picture frame','Trinket box'],
'Botanicals & florals':['Faux plant','Planter','Terrarium','Dried flowers','Vertical plant wall'],
'Hardware & trims':['Cabinet knob','Cabinet pull','Curtain rod','Switch plate','Wallpaper']};
export const slug=s=>s.toLowerCase().replaceAll(' ','_');
export function categoryOptions(){return Object.entries(groups).map(([label,items])=><optgroup key={label} label={label}>{items.map(name=><option key={name} value={slug(name)}>{name}</option>)}</optgroup>)}
