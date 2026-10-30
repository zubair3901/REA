import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
const ARTIFACTS = fileURLToPath(new URL("../test-results/", import.meta.url));
mkdirSync(ARTIFACTS, { recursive: true });
import { chromium } from "@playwright/test";
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const base = process.env.ROOMFORM_TEST_URL || "http://localhost:5177";
await page.goto(base);
await page.getByRole("heading", { name: "A space you love." }).waitFor();
const comparison = page.getByRole("slider", {
  name: "Explore the room before and after",
});
await comparison.fill("40");
await comparison.focus();
await page.keyboard.press("ArrowRight");
if ((await comparison.inputValue()) !== "41")
  throw Error("Comparison keyboard control failed");
await comparison.fill("35");
await page
  .getByRole("button", { name: "Furniture that fits", exact: true })
  .click();
if (
  (await page
    .getByRole("button", { name: "Furniture that fits", exact: true })
    .getAttribute("aria-pressed")) !== "true"
)
  throw Error("Service selection failed");
await page.screenshot({
  path: ARTIFACTS + "roomform-real-photo-home.png",
  fullPage: true,
});
await page
  .getByRole("button", { name: "Become a seller", exact: false })
  .click();
await page.locator(".manual-access summary").click();
await page
  .getByPlaceholder("Existing server-issued key")
  .fill("photo-test-key");
await page
  .getByRole("button", { name: "Load my listings", exact: true })
  .click();
await page
  .getByLabel("Upload product photographs")
  .setInputFiles(
    fileURLToPath(new URL("./fixtures/product-sofa.jpg", import.meta.url)),
  );
await page
  .getByText("Photos prepared. Review every cutout before publishing.", {
    exact: true,
  })
  .waitFor({ timeout: 60000 });
await page
  .getByLabel("Photo angle", { exact: true })
  .first()
  .selectOption("angled");
await page.locator(".photo-review input[type=checkbox]").check();
await page
  .getByRole("button", { name: "Approve this cutout", exact: true })
  .click();
await page.getByText("Cutout approved", { exact: false }).waitFor();
await page
  .locator(".photo-studio")
  .screenshot({ path: ARTIFACTS + "roomform-real-photo-preparation.png" });
const form = page.locator(".merchant-form");
for (const [name, value] of Object.entries({
  seller_id: "photo-review",
  name: "Review sample · actual green sofa",
  price: "850",
  width_cm: "220",
  height_cm: "85",
  depth_cm: "90",
  latitude: "24.86",
  longitude: "67.00",
  delivery_location: "Karachi",
  stock: "1",
  delivery_days: "3",
}))
  await form.locator("[name=" + name + "]").fill(value);
await form.locator("[name=category]").selectOption("sofa");
await page
  .getByRole("button", { name: "Publish product", exact: true })
  .click();
await page.getByText("Product published.", { exact: false }).waitFor();
await page.getByRole("button", { name: /^My inventory/ }).click();
await page.locator(".seller-listing").first().waitFor();
await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
await page.screenshot({
  path: ARTIFACTS + "roomform-seller-inventory.png",
  fullPage: true,
});
await page
  .getByRole("button", { name: "Orders & delivery", exact: true })
  .click();
await page
  .getByRole("button", { name: "Create a listing", exact: true })
  .click();
await page.getByRole("button", { name: "The collection", exact: true }).click();
await page
  .getByRole("button", { name: "View actual product photos", exact: true })
  .first()
  .click();
await page.getByRole("dialog").waitFor();
await page.locator(".photo-view-main img").waitFor();
await page.screenshot({ path: ARTIFACTS + "roomform-real-photo-gallery.png" });
await page.getByRole("button", { name: "Close product photographs" }).click();
const account = await page.request.post(base + "/api/workspace/register", {
  data: {
    name: "Photo review buyer",
    email: "photo-review-" + Date.now() + "@example.com",
    password: "photo-review-test-password",
  },
});
if (!account.ok()) throw Error(await account.text());
const project = await page.request.post(base + "/api/workspace/projects", {
  data: {
    name: "Real-photo room review",
    location: "Karachi",
    budget: 2500,
    currency: "USD",
    preference: "either",
  },
});
if (!project.ok()) throw Error(await project.text());
await page.reload();
await page.locator(".header-account").click();
await page.locator(".ws-project").first().click();
await page
  .locator(".atelier-desktop-nav")
  .getByRole("button", { name: /^Design studio/ })
  .click();
console.log("Studio opened");
await page.locator(".rf-investment input[type=checkbox]").check();
await page
  .getByRole("button", { name: "Confirm budget & find my pieces", exact: true })
  .click();
await page.locator(".rf-plan-result").waitFor();
console.log("Budget proposal ready");
await page
  .locator(".rf-empty-room input[type=file]")
  .setInputFiles(
    fileURLToPath(new URL("../public/images/living.jpg", import.meta.url)),
  );
console.log("Room uploaded");
await page.locator(".rf-generate").click();
console.log("Generation requested");
await page.locator(".room-product-marker").first().waitFor();
await page.locator(".room-product-marker").first().click();
await page
  .getByRole("button", { name: "Inspect seller photos", exact: true })
  .waitFor();
await page.getByRole("button", { name: "Full view", exact: true }).click();
await page.locator(".room-photo-result.expanded").waitFor();
await page.keyboard.press("Escape");
if (await page.locator(".room-photo-result.expanded").count())
  throw Error("Full-view Escape failed");
await page
  .getByRole("button", { name: "Draw product region", exact: true })
  .click();
await page.locator(".room-actual-image").scrollIntoViewIfNeeded();
await page.waitForTimeout(200);
const bounds = await page.locator(".room-actual-image").boundingBox();
await page.mouse.move(
  bounds.x + bounds.width * 0.2,
  bounds.y + bounds.height * 0.2,
);
await page.mouse.down();
await page.mouse.move(
  bounds.x + bounds.width * 0.6,
  bounds.y + bounds.height * 0.7,
  { steps: 8 },
);
await page.mouse.up();
await page
  .getByRole("button", { name: "Save product hotspot", exact: true })
  .click();
await page
  .getByRole("button", { name: "Compare before / after", exact: true })
  .click();
await page
  .getByRole("slider", { name: "Before and after comparison", exact: true })
  .fill("65");
await page
  .getByRole("button", { name: "Shop the result", exact: true })
  .click();
await page.evaluate(() => {
  document.activeElement?.blur();
  window.scrollTo({ top: 0, behavior: "instant" });
});
await page.waitForTimeout(150);
await page.screenshot({
  path: ARTIFACTS + "roomform-real-photo-hotspots.png",
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: ARTIFACTS + "roomform-studio-mobile.png",
  fullPage: true,
});
if (
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
)
  errors.push("Studio mobile horizontal overflow");
await page.setViewportSize({ width: 1440, height: 1000 });
await page.getByRole("button", { name: "Discover", exact: true }).click();
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: ARTIFACTS + "roomform-real-photo-mobile.png",
  fullPage: true,
});
if (
  await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
)
  errors.push("Mobile horizontal overflow");
await browser.close();
if (errors.length) throw Error(errors.join(";"));
console.log(
  "Real JPEG → neural matting → seller review → listing → public original gallery → customer budget/layout → clickable hotspot → saved region → comparison, plus mobile passed.",
);
