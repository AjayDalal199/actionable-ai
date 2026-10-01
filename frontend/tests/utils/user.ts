import { expect, type Page } from "@playwright/test"

export async function signUpNewUser(
  page: Page,
  name: string,
  email: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await page.waitForURL("/dashboard")
  await expect(page.getByRole("heading", { name: "Quick Start" })).toBeVisible()
  await logOutUser(page)
}

export async function logInUser(page: Page, email: string, password: string) {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/dashboard")
  await expect(page.getByRole("heading", { name: "Quick Start" })).toBeVisible()
}

export async function logOutUser(page: Page) {
  await page.getByRole("button", { name: "Log out" }).click()
  await page.waitForURL("/login")
}
