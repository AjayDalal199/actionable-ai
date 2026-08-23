export type CtaPlacement = "header" | "hero" | "footer_band"

export type LandingEvent =
  | { event: "landing_view" }
  | { event: "cta_get_started"; placement: CtaPlacement }
  | { event: "cta_login" }
  | { event: "nav_anchor"; target: string }

export function track(payload: LandingEvent) {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent("aa-analytics", { detail: payload }))
}
