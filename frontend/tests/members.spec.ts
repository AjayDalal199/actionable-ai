import { expect, type Page, test } from "@playwright/test"
import { findLastEmail } from "./utils/mailcatcher"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomPassword,
  randomWorkspaceName,
} from "./utils/random"
import { logInUser } from "./utils/user"

async function ensureWorkspace(page: Page) {
  const nameInput = page.getByTestId("create-workspace-name-input")
  if (await nameInput.isVisible()) {
    await nameInput.fill(randomWorkspaceName())
    await page.getByTestId("create-workspace-button").click()
    await expect(page.getByText("Workspace created")).toBeVisible()
  }
}

test.describe("Workspace members", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Admin can invite an existing user from Members", async ({ page }) => {
    const adminEmail = randomEmail()
    const adminPassword = randomPassword()
    const memberEmail = randomEmail()
    const memberPassword = randomPassword()

    await createUser({ email: adminEmail, password: adminPassword })
    await createUser({ email: memberEmail, password: memberPassword })
    await logInUser(page, adminEmail, adminPassword)
    await ensureWorkspace(page)

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard\/members/)
    await expect(
      page.getByRole("heading", { name: "Members", exact: true }),
    ).toBeVisible()
    await expect(
      page.getByRole("row").filter({ hasText: adminEmail }),
    ).toBeVisible()

    await page.getByTestId("invite-member-button").click()
    await page.getByTestId("invite-member-email-input").fill(memberEmail)
    await page.getByTestId("invite-member-submit").click()
    await expect(page.getByText("Member invited")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    const memberRow = page.getByRole("row").filter({ hasText: memberEmail })
    await expect(memberRow).toBeVisible()
    await expect(memberRow.getByText("Editor")).toBeVisible()
    await expect(page.getByTestId(`member-status-${memberEmail}`)).toHaveText(
      "Pending",
    )
  })

  test("Invited member cannot use the workspace until they accept", async ({
    page,
  }) => {
    const adminEmail = randomEmail()
    const adminPassword = randomPassword()
    const memberEmail = randomEmail()
    const memberPassword = randomPassword()

    await createUser({ email: adminEmail, password: adminPassword })
    await createUser({ email: memberEmail, password: memberPassword })
    await logInUser(page, adminEmail, adminPassword)
    await ensureWorkspace(page)

    await page.goto("/dashboard/members")
    await page.getByTestId("invite-member-button").click()
    await page.getByTestId("invite-member-email-input").fill(memberEmail)
    await page.getByTestId("invite-member-submit").click()
    await expect(page.getByText("Member invited")).toBeVisible()

    await page.getByRole("button", { name: "Log out" }).click()
    await logInUser(page, memberEmail, memberPassword)

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await expect(
      page.getByRole("heading", { name: "Create a workspace first" }),
    ).toBeVisible()
    await expect(page.getByTestId("invite-member-button")).toHaveCount(0)
  })

  test("Members asks for a workspace first", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard\/members/)
    await expect(
      page.getByRole("heading", { name: "Create a workspace first" }),
    ).toBeVisible()
    await expect(page.getByTestId("invite-member-button")).toHaveCount(0)
  })

  test("Invited member can accept from email", async ({ page, request }) => {
    test.skip(
      !process.env.MAILCATCHER_HOST,
      "MAILCATCHER_HOST is not configured",
    )
    const adminEmail = randomEmail()
    const adminPassword = randomPassword()
    const memberEmail = randomEmail()
    const memberPassword = randomPassword()

    await createUser({ email: adminEmail, password: adminPassword })
    await createUser({ email: memberEmail, password: memberPassword })
    await logInUser(page, adminEmail, adminPassword)
    await ensureWorkspace(page)

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await page.getByTestId("invite-member-button").click()
    await page.getByTestId("invite-member-email-input").fill(memberEmail)
    await page.getByTestId("invite-member-submit").click()
    await expect(page.getByText("Member invited")).toBeVisible()

    const emailData = await findLastEmail({
      request,
      filter: (e) => e.recipients.includes(`<${memberEmail}>`),
    })
    await page.goto(
      `${process.env.MAILCATCHER_HOST}/messages/${emailData.id}.html`,
    )
    const url = await page.getAttribute(
      'a[href*="/join-workspace?token="]',
      "href",
    )
    const joinUrl = new URL(url!)
    await page.goto(`${joinUrl.pathname}${joinUrl.search}`)
    await page.getByTestId("accept-invite-button").click()
    await expect(page.getByText("Invite accepted")).toBeVisible()

    await page.getByTestId("user-menu").click()
    await page.getByTestId("logout-button").click()
    await logInUser(page, memberEmail, memberPassword)
    await page.getByRole("link", { name: "Members", exact: true }).click()
    await expect(page.getByTestId(`member-status-${memberEmail}`)).toHaveText(
      "Accepted",
    )
    await expect(page.getByTestId("invite-member-button")).toHaveCount(0)
  })

  test("New invited user lands on the dashboard after setting a password", async ({
    page,
    request,
  }) => {
    test.skip(
      !process.env.MAILCATCHER_HOST,
      "MAILCATCHER_HOST is not configured",
    )
    const adminEmail = randomEmail()
    const adminPassword = randomPassword()
    const memberEmail = randomEmail()
    const memberPassword = randomPassword()

    await createUser({ email: adminEmail, password: adminPassword })
    await logInUser(page, adminEmail, adminPassword)
    await ensureWorkspace(page)

    await page.getByRole("link", { name: "Members", exact: true }).click()
    await page.getByTestId("invite-member-button").click()
    await page.getByTestId("invite-member-email-input").fill(memberEmail)
    await page.getByTestId("invite-member-submit").click()
    await expect(page.getByText("Member invited")).toBeVisible()

    await page.getByTestId("user-menu").click()
    await page.getByTestId("logout-button").click()

    const emailData = await findLastEmail({
      request,
      filter: (e) => e.recipients.includes(`<${memberEmail}>`),
    })
    await page.goto(
      `${process.env.MAILCATCHER_HOST}/messages/${emailData.id}.html`,
    )
    const url = await page.getAttribute(
      'a[href*="/join-workspace?token="]',
      "href",
    )
    const joinUrl = new URL(url!)
    await page.goto(`${joinUrl.pathname}${joinUrl.search}`)
    await page.getByTestId("join-password-input").fill(memberPassword)
    await page.getByTestId("join-confirm-password-input").fill(memberPassword)
    await page.getByTestId("accept-invite-button").click()
    await expect(page.getByText("Invite accepted")).toBeVisible()
    await expect(page).toHaveURL(/\/dashboard\/?$/)
    await expect(
      page.getByRole("heading", { name: "Quick Start" }),
    ).toBeVisible()
    await expect(page.getByTestId("user-menu")).toContainText(memberEmail)
  })
})
