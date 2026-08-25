import { expect, test } from "@playwright/test"

import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomPassword,
  randomWorkspaceName,
} from "./utils/random"
import { logInUser } from "./utils/user"

const productNav = ["Dashboard", "Knowledge", "Tools", "Chat", "Members"]

test("Product nav replaces the template Items dashboard", async ({ page }) => {
  await page.goto("/dashboard")

  for (const name of productNav) {
    await expect(page.getByRole("link", { name, exact: true })).toBeVisible()
  }
  await expect(
    page.getByRole("link", { name: "Admin", exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Items", exact: true }),
  ).toHaveCount(0)
  await expect(
    page.getByRole("link", { name: "Settings", exact: true }),
  ).toHaveCount(0)
  await page.getByTestId("user-menu").click()
  await expect(
    page.getByRole("menuitem", { name: "User Settings" }),
  ).toBeVisible()
  await expect(page.getByRole("menuitem", { name: "Members" })).toHaveCount(0)
  await expect(page.getByRole("heading", { name: "Quick Start" })).toBeVisible()
  await expect(
    page.getByText("Name your workspace → upload a doc → ask a question"),
  ).toBeVisible()
  await expect(page.getByTestId("workspace-switcher")).toBeVisible()
  await page.getByTestId("workspace-switcher").click()
  await expect(page.getByRole("menuitem", { name: "Members" })).toHaveCount(0)
})

test("Knowledge, Tools, Chat, and Members are reachable from the sidebar", async ({
  page,
}) => {
  await page.goto("/dashboard")

  await page.getByRole("link", { name: "Knowledge", exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard\/knowledge/)
  await expect(
    page.getByRole("heading", { name: "Knowledge", exact: true }),
  ).toBeVisible()
  await expect(page.getByText("Your AI has no knowledge yet")).toBeVisible()

  await page.getByRole("link", { name: "Tools", exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard\/tools/)
  await expect(
    page.getByRole("heading", { name: "Tools", exact: true }),
  ).toBeVisible()

  await page.getByRole("link", { name: "Chat", exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard\/chat/)
  await expect(
    page.getByRole("heading", { name: "Chat", exact: true }),
  ).toBeVisible()

  await page.getByRole("link", { name: "Members", exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard\/members/)
  await expect(
    page.getByRole("heading", { name: "Members", exact: true }),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "User Settings" }).click()
  await expect(page).toHaveURL(/\/dashboard\/settings/)
  await expect(
    page.getByRole("heading", { name: "User Settings" }),
  ).toBeVisible()
})

test.describe("Workspace empty state", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("User without a workspace can name one from Quick Start", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    const workspaceName = randomWorkspaceName()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await expect(
      page.getByRole("button", { name: "Create workspace" }),
    ).toBeVisible()
    await expect(
      page.getByRole("button", { name: "Go to Knowledge" }),
    ).toBeDisabled()
    await expect(
      page.getByRole("button", { name: "Go to Chat" }),
    ).toBeDisabled()

    await page.getByTestId("create-workspace-name-input").fill(workspaceName)
    await page.getByTestId("create-workspace-button").click()

    await expect(page.getByText("Workspace created")).toBeVisible()
    await expect(
      page.getByRole("button", { name: "Create workspace" }),
    ).toHaveCount(0)
    await expect(page.getByTestId("workspace-switcher")).toContainText(
      workspaceName,
    )

    await page.getByRole("link", { name: "Go to Knowledge" }).click()
    await expect(page).toHaveURL(/\/dashboard\/knowledge/)
    await expect(page.getByText("Your AI has no knowledge yet")).toBeVisible()
  })

  test("Knowledge, Tools, Chat, and Members ask for a workspace first", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.getByRole("link", { name: "Knowledge", exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard\/knowledge/)
    await expect(
      page.getByRole("heading", { name: "Create a workspace first" }),
    ).toBeVisible()
    await expect(
      page.getByText(
        "Name a workspace on Quick Start before you can use Knowledge.",
      ),
    ).toBeVisible()

    await page.getByRole("link", { name: "Tools", exact: true }).click()
    await expect(
      page.getByText(
        "Name a workspace on Quick Start before you can use Tools.",
      ),
    ).toBeVisible()

    await page.getByRole("link", { name: "Chat", exact: true }).click()
    await expect(
      page.getByText(
        "Name a workspace on Quick Start before you can use Chat.",
      ),
    ).toBeVisible()

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await expect(
      page.getByText(
        "Name a workspace on Quick Start before you can use Members.",
      ),
    ).toBeVisible()

    await page.getByRole("link", { name: "Go to Quick Start" }).click()
    await expect(page).toHaveURL(/\/dashboard\/?$/)
    await expect(
      page.getByRole("button", { name: "Create workspace" }),
    ).toBeVisible()
  })
})
