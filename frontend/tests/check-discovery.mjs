import { chromium, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
const artifacts = fileURLToPath(new URL("../test-results/", import.meta.url));
mkdirSync(artifacts, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const base = process.env.ROOMFORM_TEST_URL || "http://localhost:5173";
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
page.setDefaultTimeout(15000);
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
try {
  await page.goto(base);
  await page.evaluate(() => document.fonts.ready);
  await expect(
    page.getByRole("heading", { name: /A space you love/ }),
  ).toBeVisible();
  const slider = page.getByRole("slider", {
    name: "Explore the room before and after",
  });
  await slider.fill("70");
  await slider.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(slider).toHaveValue("69");
  await slider.fill("35");
  for (const image of await page
    .locator(".hero-comparison img")
    .evaluateAll((images) => images.map((i) => i.getAttribute("src"))))
    if (image.endsWith(".gif"))
      throw Error("Hero must remain a simple image slider");
  await page.locator(".app-rail-pages").getByRole("button", { name: "Inspiration", exact: true }).click();
  const demo = page.locator(".transformation-card").first();
  await demo.scrollIntoViewIfNeeded();
  await expect(demo.locator(".transformation-media>img")).toHaveAttribute(
    "src",
    "/demos/living.gif",
  );
  await expect(demo.locator(".transformation-media>img")).toHaveJSProperty(
    "naturalWidth",
    560,
  );
  await demo
    .getByRole("button", {
      name: "Pause From empty to inviting animation",
      exact: true,
    })
    .click();
  await expect(demo.locator(".transformation-media>img")).toHaveAttribute(
    "src",
    "/demos/living-poster.jpg",
  );
  await demo
    .getByRole("button", {
      name: "Play From empty to inviting animation",
      exact: true,
    })
    .click();
  await expect(demo.locator(".transformation-media>img")).toHaveAttribute(
    "src",
    "/demos/living.gif",
  );
  await page
    .locator(".app-rail-pages")
    .getByRole("button", { name: "Inspiration", exact: true })
    .click();
  await expect(page).toHaveURL(/page=inspiration/);
  await expect(page.locator(".curated-card")).toHaveCount(24);
  const records = await (await page.request.get(base + "/inspiration/curated.json")).json();
  const filters = page.getByRole("group", { name: "Inspiration categories" });
  await expect(filters.getByRole("button")).toHaveCount(11);
  const populated = [...new Set(records.map(item => item.category))];
  const labels = { living:"Living room", bedroom:"Bedroom", kitchen:"Kitchen", office:"Office", dining:"Dining room", garden:"Garden", landscape:"Landscape", exterior:"Exterior", bathroom:"Bathroom", restaurant:"Restaurants" };
  for (const category of populated) {
    await filters.getByRole("button", { name: new RegExp("^" + labels[category]) }).click();
    await expect(page.locator(".curated-card")).toHaveCount(Math.min(24, records.filter(item => item.category === category).length));
    await expect(page.locator(".curated-card").first().getByRole("button", { name:"Design this", exact:true })).toBeVisible();
  }
  await filters.getByRole("button", { name:/^All spaces/ }).click();
  await page.getByLabel("Search inspiration").fill("zzzz-no-matching-reference");
  await expect(page.locator(".curated-card")).toHaveCount(0);
  await page.getByLabel("Search inspiration").fill("");
  await expect(page.locator(".curated-card")).toHaveCount(24);
  await page.locator(".curated-card").first().getByRole("button", { name:"Design this", exact:true }).click();
  await expect(page).toHaveURL(/page=studio/);
  await page.goBack();
  await expect(page).toHaveURL(/page=inspiration/);
  await page.reload();
  await expect(page.getByRole("heading", { name:/Find a look you love/ })).toBeVisible();
  await expect(page.locator(".curated-card")).toHaveCount(24);
  await page.evaluate(() => {
    document.activeElement?.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: artifacts + "discovery-inspiration-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Roomform home", exact: true }).click();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.waitForTimeout(150);
  await page.screenshot({
    path: artifacts + "discovery-home-desktop.png",
    fullPage: true,
  });
  await page.screenshot({
    path: artifacts + "discovery-home-first-screen.png",
  });
  const faq = page.locator(".design-faq details").first();
  await faq.locator("summary").click();
  await expect(faq).toHaveAttribute("open", "");
  for (const width of [1440, 1024, 768, 390, 360]) {
    await page.setViewportSize({ width, height: 900 });
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      )
    )
      errors.push("Homepage overflow at " + width);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({
    path: artifacts + "discovery-home-mobile.png",
    fullPage: true,
  });
  for (const name of [
    "Inspiration",
    "Sell with us",
    "Real furniture",
    "For business",
    "Local professionals",
    "Talk to a designer",
    "My projects",
  ]) {
    await page.getByRole("button", { name: "Open menu", exact: true }).click();
    await page
      .locator(".atelier-menu")
      .getByRole("button", { name, exact: true })
      .click();
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      )
    )
      errors.push(name + " mobile overflow");
  }
  await page.getByRole("button", { name: "Open menu", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(page.locator(".atelier-menu")).toHaveCount(0);
  const reduced = await browser.newContext({
    reducedMotion: "reduce",
    viewport: { width: 390, height: 844 },
  });
  const still = await reduced.newPage();
  await still.goto(base + "/?page=inspiration");
  await still.locator(".transformation-card").first().scrollIntoViewIfNeeded();
  await expect(
    still.locator(".transformation-media>img").first(),
  ).toHaveAttribute("src", "/demos/living-poster.jpg");
  await expect(
    still.getByRole("button", {
      name: "Play From empty to inviting animation",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "false");
  await reduced.close();
  if (errors.length) throw Error(errors.join("; "));
  console.log(
    "Discovery checks passed: GIF load/pause/play, reduced motion, curated inspiration filters, design entry, back/reload, FAQ, responsive navigation and overflow.",
  );
} finally {
  await browser.close();
}
