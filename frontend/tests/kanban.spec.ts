import { expect, test, type Page } from "@playwright/test";

const mockBoard = {
  columns: [
    { id: "col-1", title: "Backlog",      cardIds: ["card-1", "card-2"] },
    { id: "col-2", title: "Discovery",    cardIds: ["card-3"] },
    { id: "col-3", title: "In Progress",  cardIds: ["card-4", "card-5"] },
    { id: "col-4", title: "Review",       cardIds: ["card-6"] },
    { id: "col-5", title: "Done",         cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Align roadmap themes",   details: "Draft themes." },
    "card-2": { id: "card-2", title: "Gather customer signals", details: "Review feedback." },
    "card-3": { id: "card-3", title: "Prototype analytics",    details: "Sketch layouts." },
    "card-4": { id: "card-4", title: "Refine status language",  details: "Standardize labels." },
    "card-5": { id: "card-5", title: "Design card layout",      details: "Add hierarchy." },
    "card-6": { id: "card-6", title: "QA micro-interactions",   details: "Verify states." },
    "card-7": { id: "card-7", title: "Ship marketing page",     details: "Assets delivered." },
    "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Release notes." },
  },
};

test.beforeEach(async ({ page }) => {
  await page.route("/api/auth/login", async (route) => {
    const body = await route.request().postDataJSON();
    if (body.username === "user" && body.password === "password") {
      await route.fulfill({ json: { token: "test-token" } });
    } else {
      await route.fulfill({ status: 401, json: { detail: "Invalid credentials" } });
    }
  });
  await page.route("/api/auth/logout", async (route) => {
    await route.fulfill({ json: { ok: true } });
  });
  await page.route("/api/board", async (route) => {
    await route.fulfill({ json: mockBoard });
  });
  await page.route("/api/columns/**", async (route) => {
    await route.fulfill({ json: { ok: true } });
  });
  await page.route("/api/cards", async (route) => {
    const body = await route.request().postDataJSON();
    await route.fulfill({
      status: 201,
      json: { id: "card-new", title: body.title, details: body.details ?? "" },
    });
  });
  await page.route("/api/cards/**", async (route) => {
    await route.fulfill({ status: route.request().method() === "DELETE" ? 204 : 200, json: { ok: true } });
  });
});

async function loginAndGoToBoard(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForSelector('[data-testid^="column-"]');
}

test("shows login form on first visit", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("wrong credentials shows error", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByText(/invalid username or password/i)).toBeVisible();
});

test("loads the kanban board after login", async ({ page }) => {
  await loginAndGoToBoard(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("logout returns to login page", async ({ page }) => {
  await loginAndGoToBoard(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
});

test("adds a card to a column", async ({ page }) => {
  await loginAndGoToBoard(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await loginAndGoToBoard(page);
  const card = page.getByTestId("card-card-1");
  // Review column is index 3 (col-4)
  const targetColumn = page.locator('[data-testid^="column-"]').nth(3);
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) throw new Error("Unable to resolve drag coordinates.");

  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(columnBox.x + columnBox.width / 2, columnBox.y + 120, { steps: 12 });
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});
