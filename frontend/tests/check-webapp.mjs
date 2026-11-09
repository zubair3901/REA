import {chromium,expect} from '@playwright/test';
const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
const p=await b.newPage({viewport:{width:1440,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
try {
 await p.goto('http://localhost:5173'); await p.evaluate(()=>document.fonts.ready);
 await expect(p.getByRole('navigation',{name:'Workspace navigation'})).toBeVisible();
 await expect(p.locator('.app-design-category')).toHaveCount(4);
 await p.getByRole('link',{name:/Load more Inspirations/}).click();await expect(p).toHaveURL(/page=inspiration/);
 await expect(p.getByRole('group',{name:'Inspiration categories'}).getByRole('button')).toHaveCount(11);
 await p.setViewportSize({width:375,height:812});const nav=p.getByRole('navigation',{name:'Mobile app navigation'});await expect(nav).toBeVisible();await expect(nav.getByRole('button')).toHaveCount(5);
 await nav.getByRole('button',{name:'Home',exact:true}).click();await expect(p).toHaveURL(/localhost:5173\/$/);
 await nav.getByRole('button',{name:'Design',exact:true}).click();await expect(p).toHaveURL(/page=studio/);await p.goBack();
 expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await p.screenshot({path:'test-results/webapp-mobile.png'});await p.setViewportSize({width:1440,height:1000});await p.screenshot({path:'test-results/webapp-desktop.png'});
 expect(errors).toEqual([]);console.log('Web app checks passed: rail, categories, gallery route, mobile tabs, back history, overflow.');
} finally {await b.close();}
