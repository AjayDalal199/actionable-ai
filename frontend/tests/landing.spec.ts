import { expect, test } from "@playwright/test"

test.use({ storageState: { cookies: [], origins: [] } })

test("landing page shows the product promise", async ({ page }) => {
  await page.goto("/")

  await expect(page).toHaveTitle(/Actionable AI/)
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Give your product an agent that can actually do things.",
    }),
  ).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Get started for free" }).first(),
  ).toBeVisible()
})

test("hero CTA goes to signup", async ({ page }) => {
  await page.goto("/")

  await page.getByRole("link", { name: "Get started for free" }).first().click()
  await page.waitForURL("/signup")
})

test("header log in goes to login", async ({ page }) => {
  await page.goto("/")

  await page.getByRole("navigation", { name: "Page" }).waitFor()
  await page.getByRole("link", { name: "Log in" }).first().click()
  await page.waitForURL("/login")
})

test("landing appearance can switch to light", async ({ page }) => {
  await page.goto("/")

  await page.getByTestId("theme-button").click()
  await page.getByTestId("light-mode").click()
  await expect(page.locator("html")).not.toHaveClass(/dark/)
})

test("privacy and terms routes render", async ({ page }) => {
  await page.goto("/privacy")
  await expect(
    page.getByRole("heading", { name: "Privacy Policy" }),
  ).toBeVisible()

  await page.goto("/terms")
  await expect(
    page.getByRole("heading", { name: "Terms of Service" }),
  ).toBeVisible()
})
