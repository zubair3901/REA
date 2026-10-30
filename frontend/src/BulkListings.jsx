import React,{useState} from 'react';
const API=(import.meta.env.VITE_API_URL||'').replace(/\/$/,'');
export default function BulkListings({token,sellerId,onPublished}){
 const [manifest,setManifest]=useState(null),[photos,setPhotos]=useState([]),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[id,setId]=useState('');
 async function call(path,options){const r=await fetch(API+path,{...options,headers:{...options.headers,'X-Merchant-Key':token}});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Check each product’s required fields and valid values.');return d}
 async function publish(e){e.preventDefault();setBusy(true);setMessage('');try{
  if(!token)throw Error('Sign in before uploading a batch.');
  if(!manifest||manifest.size>1024*1024)throw Error('Choose a JSON manifest under 1 MB.');
  const data=JSON.parse(await manifest.text());
  if(!Array.isArray(data)||!data.length||data.length>100)throw Error('The manifest must contain 1–100 products.');
  if(photos.reduce((n,f)=>n+f.size,0)>50*1024*1024)throw Error('Keep each batch under 50 MB of photos.');
  const map=new Map(photos.map(f=>[f.name,f]));const rows=[];
  for(let i=0;i<data.length;i++){
   const row={...data[i]},photo=map.get(row.image_file);if(!photo)throw Error('Product '+(i+1)+': missing image_file in the chosen photos.');
   setMessage('Uploading product '+(i+1)+' of '+data.length+'…');
   const f=new FormData();f.append('file',photo);const result=await call('/api/uploads',{method:'POST',body:f});
   delete row.image_file;rows.push({...row,seller_id:sellerId||id,image_url:result.image_url});
  }
  const result=await call('/api/seller/listings/bulk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({assets:rows})});
  setMessage(result.created+' products published.');await onPublished();
 }catch(e){setMessage(e.message)}finally{setBusy(false)}}
 return <section className="seller-inventory"><h2>Publish a collection</h2><p className="seller-guidance">Upload a JSON array with each product’s name, category, style, price, currency, dimensions, condition, location, stock and delivery details. Add image_file matching an uploaded transparent product photo’s filename. Up to 100 products and 50 MB per batch. Images upload first; listings publish together after validation.</p><a className="rf-text-button" href="/supplier-manifest.example.json" download>Download manifest example</a><form onSubmit={publish}><fieldset disabled={busy||!token} style={{marginTop:18}}>{!sellerId&&<label>Seller ID<input required value={id} onChange={e=>setId(e.target.value)}/></label>}<div className="form-row"><label>Product manifest · JSON<input type="file" accept=".json,application/json" required onChange={e=>setManifest(e.target.files[0])}/></label><label>Transparent product photos<input type="file" accept="image/png,image/webp" multiple required onChange={e=>setPhotos([...e.target.files])}/></label></div><button className="rf-primary" disabled={busy||!token} style={{marginTop:18}}>{busy?'Publishing collection…':'Publish collection'}</button></fieldset></form>{message&&<p role="status" className="seller-message">{message}</p>}</section>
}
