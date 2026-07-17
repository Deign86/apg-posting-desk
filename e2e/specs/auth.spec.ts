const ADMIN = { email: "admin@apg.local", password: "admin@123" };
const OPERATOR = { email: "operator@apg.local", password: "oper@123" };

async function loginAs(page, creds) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.fill("#loginEmail", creds.email);
  await page.fill("#loginPassword", creds.password);
  await page.click("#loginSubmit");
  await page.waitForFunction(
    () => document.getElementById("loginScreen")?.hidden === true,
    { timeout: 5000 }
  );
}

test.describe("Login screen", () => {
  test("renders email, password, submit, and theme toggle", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("#loginScreen")).toBeVisible();
    await expect(page.locator("#loginEmail")).toBeVisible();
    await expect(page.locator("#loginPassword")).toBeVisible();
    await expect(page.locator("#loginSubmit")).toBeVisible();
    await expect(page.locator("#loginThemeToggle")).toBeVisible();
  });

  test("shows error on invalid credentials", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "wrong@apg.local");
    await page.fill("#loginPassword", "wrong");
    await page.click("#loginSubmit");
    await expect(page.locator("#loginError")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("#loginError")).toHaveText(/invalid/i);
    await expect(page.locator("#loginScreen")).toBeVisible();
  });

  test("signs in as admin and shows app content", async ({ page }) => {
    await loginAs(page, ADMIN);
    await expect(page.locator("#appContent")).toBeVisible();
    await expect(page.locator("#sessionTitle")).toContainText("Signed in");
  });

  test("admin sees admin-only buttons", async ({ page }) => {
    await loginAs(page, ADMIN);
    await expect(page.locator("#newJobBtn")).toBeVisible();
    await expect(page.locator("#newJobBtn")).not.toBeHidden();
    await expect(page.locator("#processNext")).toBeVisible();
  });

  test("operator has admin-only buttons hidden", async ({ page }) => {
    await loginAs(page, OPERATOR);
    await expect(page.locator("#newJobBtn")).toBeHidden();
    await expect(page.locator("#processNext")).toBeHidden();
  });

  test("sign out returns to login screen", async ({ page }) => {
    await loginAs(page, ADMIN);
    await page.click("#signOutButton");
    await expect(page.locator("#loginScreen")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("#appContent")).toBeHidden();
  });
});

test.describe("Session API", () => {
  test("returns user info after admin login", async ({ page }) => {
    await loginAs(page, ADMIN);
    const data = await page.evaluate(async () => {
      const r = await fetch("/api/session", {
        headers: { "X-Demo-Role": "admin" },
      });
      return r.json();
    });
    expect(data.user).toBeDefined();
    expect(data.user.role).toBe("admin");
    expect(data.user.email).toBe("admin@apg.local");
  });
});
