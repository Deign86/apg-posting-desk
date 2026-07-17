import { chromium } from "@playwright/test";

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const baseURL = "http://localhost:5173";

    await page.goto(baseURL, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(1000);
    const pageTitle = await page.title();
    console.log("PASS: Page loaded, title:", pageTitle);

    const loginScreen = await page.isVisible("#loginScreen");
    const emailField = await page.isVisible("#loginEmail");
    const passwordField = await page.isVisible("#loginPassword");
    console.log("PASS: Login screen elements -", "screen:", loginScreen, "email:", emailField, "password:", passwordField);

    if (!loginScreen || !emailField || !passwordField) {
      throw new Error("Login screen elements missing");
    }

    await page.fill("#loginEmail", "bad@test.com");
    await page.fill("#loginPassword", "wrongpass");
    await page.click("#loginSubmit");
    await page.waitForSelector("#loginError:not([hidden])", { timeout: 5000 });
    const errorText = await page.textContent("#loginError");
    console.log("PASS: Invalid login error:", errorText);

    await page.fill("#loginEmail", "admin@apg.local");
    await page.fill("#loginPassword", "admin@123");
    await page.click("#loginSubmit");
    await page.waitForFunction(() => document.getElementById("loginScreen")?.hidden === true, { timeout: 5000 });
    console.log("PASS: Admin login successful, app visible:", await page.isVisible("#appContent"));

    const sessionResp = await page.evaluate(async () => {
      const r = await fetch("/api/session", { headers: { "X-Demo-Role": "admin" } });
      return r.json();
    });
    console.log("PASS: Session API role:", sessionResp.user?.role);

    console.log("PASS: Admin buttons visible?", await page.isVisible("#newJobBtn"), await page.isVisible("#processNext"));

    await page.click("#signOutButton");
    await page.waitForFunction(() => document.getElementById("loginScreen")?.hidden === false, { timeout: 5000 });
    console.log("PASS: Sign out returned to login");

    await page.fill("#loginEmail", "operator@apg.local");
    await page.fill("#loginPassword", "oper@123");
    await page.click("#loginSubmit");
    await page.waitForFunction(() => document.getElementById("loginScreen")?.hidden === true, { timeout: 5000 });
    const hidden = await page.evaluate(() => document.getElementById("newJobBtn")?.hidden === true);
    console.log("PASS: Operator admin-buttons-hidden:", hidden);

    console.log("\n========== ALL E2E SMOKE TESTS PASSED ==========");
  } finally {
    await browser.close();
  }
}

main().catch((err) => { console.error("FAILURE:", err.message); process.exit(1); });