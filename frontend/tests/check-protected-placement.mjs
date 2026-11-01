// Actual local auth/catalog/project flow; model readiness and final POST are
// simulated. This verifies controls/transport, not live AI image quality.
import { chromium, expect } from "@playwright/test";
import { fileURLToPath } from "node:url";
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const base = process.env.ROOMFORM_TEST_URL || "http://localhost:5173";
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(20000);
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
try {
  await page.route("**/api/models", (r) =>
    r.fulfill({
      json: [
        { id: "composite", label: "Photo layout", available: true },
        { id: "gemini", label: "Gemini", available: true },
      ],
    }),
  );
  await page.route("**/api/placement/capabilities", (r) =>
    r.fulfill({ json: { enabled: true, perception_configured: true } }),
  );
  await page.goto(base);
  const account = await page.request.post(base + "/api/workspace/register", {
    data: {
      name: "Measured UI test",
      email: "measured-ui-" + Date.now() + "@example.com",
      password: "measured-ui-test-password",
    },
  });
  if (!account.ok()) throw Error(await account.text());
  const project = await page.request.post(base + "/api/workspace/projects", {
    data: {
      name: "Measured calibration check",
      location: "Karachi",
      budget: 2500,
      currency: "USD",
      preference: "either",
    },
  });
  if (!project.ok()) throw Error(await project.text());
  const saved = await project.json();
  await page.evaluate(
    (id) => sessionStorage.setItem("roomform-project", id),
    saved.id,
  );
  await page.reload();
  await page
    .locator(".atelier-desktop-nav")
    .getByRole("button", { name: /^Design studio/ })
    .click();
  await page.locator(".rf-product-picker .rf-product").first().click();
  await page.locator(".rf-investment input[type=checkbox]").check();
  await page
    .locator(".rf-empty-room input[type=file]")
    .setInputFiles(
      fileURLToPath(new URL("../public/images/living.jpg", import.meta.url)),
    );
  const toggle = page.locator(".protected-workflow-choice input");
  await expect(toggle).toBeChecked();
  await page.locator(".protected-calibration").scrollIntoViewIfNeeded();
  const bounds = await page.locator(".protected-calibration").boundingBox();
  for (const [x, y] of [
    [0.15, 0.4],
    [0.85, 0.4],
    [0.95, 0.95],
    [0.05, 0.95],
  ])
    await page.mouse.click(
      bounds.x + bounds.width * x,
      bounds.y + bounds.height * y,
    );
  await expect(
    page.getByText("4/4 floor corners marked", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Measured floor width", { exact: true }).fill("600");
  await page.getByLabel("Measured floor depth", { exact: true }).fill("600");
  await page
    .getByLabel("I measured this floor rectangle.", { exact: false })
    .check();
  await page.getByLabel("I agree to send my room", { exact: false }).check();
  await expect(page.locator(".rf-generate")).toBeEnabled();
  let posted = false;
  await page.route("**/api/designs", async (route) => {
    const body = route.request().postData();
    if (
      !body.includes('name="pipeline"\r\n\r\nprotected') ||
      !body.includes('"measurement_confirmed":true') ||
      !body.includes('"floor_width_cm":600')
    )
      throw Error("Missing measured pipeline request fields");
    posted = true;
    await route.fulfill({
      status: 422,
      json: {
        detail:
          "Simulated pipeline boundary check; no external inference sent.",
      },
    });
  });
  await page.locator(".rf-generate").click();
  await expect(page.getByRole("alert")).toContainText(
    "Simulated pipeline boundary check",
  );
  if (!posted) throw Error("No protected request posted");
  await page.setViewportSize({ width: 390, height: 844 });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    errors.push("Measured editor mobile overflow");
  if (errors.length) throw Error(errors.join("; "));
  console.log(
    "Measured UI passed: real account/project/catalog, floor corners, dimensions, confirmation, consent and protected multipart payload. AI readiness/POST simulated.",
  );
} finally {
  await browser.close();
}
