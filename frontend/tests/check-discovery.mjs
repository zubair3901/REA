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
    .locator(".atelier-desktop-nav")
    .getByRole("button", { name: "Inspiration", exact: true })
    .click();
  await expect(page).toHaveURL(/page=inspiration/);
  await expect(page.locator(".inspiration-tile")).toHaveCount(24);
  const index = await (
    await page.request.get(base + "/inspiration/index.json")
  ).json();
  if (index.categories.length !== 10)
    throw Error("Expected ten inspiration categories");
  const hashes = new Set();
  for (const category of index.categories) {
    const records = await (await page.request.get(base + category.file)).json();
    if (records.length < 101 || records.length !== category.count)
      throw Error("Not enough real references: " + category.id);
    for (const record of records) {
      if (hashes.has(record.sha1))
        throw Error("Duplicate source image counted twice");
      hashes.add(record.sha1);
      if (!record.creator || !record.license || !record.source_url)
        throw Error("Missing attribution");
    }
    await page
      .getByRole("group", { name: "Inspiration categories" })
      .getByRole("button", { name: new RegExp("^" + category.label) })
      .click();
    await expect(page.locator(".inspiration-tile")).toHaveCount(24);
    const card = page.locator(".inspiration-tile").first();
    await expect(card.getByRole("button")).toHaveCount(1);
    await expect(
      card.getByRole("button", { name: "Design this", exact: true }),
    ).toBeVisible();
  }
  const first = await page.locator(".inspiration-tile h3").first().innerText();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Page 2 of 5", { exact: true })).toBeVisible();
  if (
    first === (await page.locator(".inspiration-tile h3").first().innerText())
  )
    throw Error("Pagination repeats same references");
  await page.getByRole("button", { name: "Previous", exact: true }).click();
  await page
    .getByLabel("Search this inspiration category")
    .fill("zzzz-no-matching-reference");
  await expect(page.locator(".inspiration-tile")).toHaveCount(0);
  await page.getByLabel("Search this inspiration category").fill("");
  await expect(page.locator(".inspiration-tile")).toHaveCount(24);
  await page
    .locator(".inspiration-tile")
    .first()
    .getByRole("button", { name: "Design this", exact: true })
    .click();
  await expect(page).toHaveURL(/page=studio/);
  await page.goBack();
  await expect(page).toHaveURL(/page=inspiration/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: /A world of ideas/ }),
  ).toBeVisible();
  await expect(page.locator(".inspiration-tile")).toHaveCount(24);
  await page.evaluate(() => {
    document.activeElement?.blur();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.screenshot({
    path: artifacts + "discovery-inspiration-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Roomform home", exact: true }).click();
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
  await still.goto(base);
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
    "Discovery checks passed: GIF load/pause/play, reduced motion, inspiration filters, design entry, back/reload, FAQ, responsive navigation and overflow.",
  );
} finally {
  await browser.close();
}
