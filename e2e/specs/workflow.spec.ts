const ADMIN = { email: "admin@apg.local", password: "admin@123" };

async function loginAsAdmin(page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.fill("#loginEmail", ADMIN.email);
  await page.fill("#loginPassword", ADMIN.password);
  await page.click("#loginSubmit");
  await page.waitForFunction(
    () => document.getElementById("loginScreen")?.hidden === true,
    { timeout: 5000 }
  );
}

test.describe("5-tab workflow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("workflow progress guide lists operator steps", async ({ page }) => {
    await expect(page.locator("text=Workflow Progress Guide")).toBeVisible();
    await expect(page.locator("text=Step 1: Download photos")).toBeVisible();
    await expect(page.locator("text=Step 2: Copy the caption")).toBeVisible();
    await expect(page.locator("text=Step 3: Post to Facebook")).toBeVisible();
    await expect(page.locator("text=Step 4: Paste the live post URL")).toBeVisible();
    await expect(page.locator("text=Step 5: Log the post")).toBeVisible();
  });

  test("sidebar shows PROPERTY LIST", async ({ page }) => {
    await expect(page.locator("text=PROPERTY LIST")).toBeVisible();
  });

  test("all five tab headings are rendered", async ({ page }) => {
    await expect(page.locator("text=Property details")).toBeVisible();
    await expect(page.locator("text=Property photos")).toBeVisible();
    await expect(page.locator("text=Caption drafting")).toBeVisible();
    await expect(page.locator("text=Facebook posting")).toBeVisible();
    await expect(page.locator("text=Post log")).toBeVisible();
  });

  test("caption guidance copy appears in caption tab", async ({ page }) => {
    await expect(page.locator("text=No emojis")).toBeVisible();
    await expect(page.locator("text=Caption source file")).toBeVisible();
    await expect(page.locator("#generateCaption")).toBeVisible();
  });

  test("dashboard metrics are rendered", async ({ page }) => {
    await expect(page.locator("text=Assigned today")).toBeVisible();
    await expect(page.locator("text=Waiting approval")).toBeVisible();
    await expect(page.locator("text=Ready to post")).toBeVisible();
    await expect(page.locator("text=Posted today")).toBeVisible();
  });

  test("toggle theme is interactive", async ({ page }) => {
    const toggle = page.locator("text=Toggle theme").first();
    await expect(toggle).toBeVisible();
    await toggle.click();
    await toggle.click();
    await expect(toggle).toBeVisible();
  });
});
