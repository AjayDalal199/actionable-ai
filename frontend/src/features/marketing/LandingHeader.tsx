import { Link } from "@tanstack/react-router"
import { Menu, X } from "lucide-react"
import { useId, useRef } from "react"

import { track } from "@/features/marketing/analytics"
import { Appearance } from "@/shared/components/Appearance"
import { Logo } from "@/shared/components/Logo"
import { Button } from "@/shared/ui/button"

const NAV = [
  { label: "How it works", hash: "how-it-works" },
  { label: "Features", hash: "features" },
  { label: "Security", hash: "security" },
  { label: "FAQ", hash: "faq" },
] as const

export function LandingHeader() {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  const openNav = () => dialogRef.current?.showModal()
  const closeNav = () => dialogRef.current?.close()

  return (
    <header className="bg-background sticky top-0 z-40">
      <div className="page-content flex h-16 items-center gap-8 border-b">
        <Logo to="/" />
        <nav className="hidden items-center gap-6 lg:flex" aria-label="Page">
          {NAV.map((item) => (
            <Link
              key={item.hash}
              to="/"
              hash={item.hash}
              className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors duration-150"
              onClick={() => track({ event: "nav_anchor", target: item.hash })}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Appearance />
          <div className="hidden items-center gap-2 lg:flex">
            <Button variant="ghost" size="lg" asChild>
              <Link to="/login" onClick={() => track({ event: "cta_login" })}>
                Log in
              </Link>
            </Button>
            <Button size="lg" asChild>
              <Link
                to="/signup"
                onClick={() =>
                  track({ event: "cta_get_started", placement: "header" })
                }
              >
                Get started
              </Link>
            </Button>
          </div>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="lg:hidden"
            aria-label="Open menu"
            onClick={openNav}
          >
            <Menu />
          </Button>
        </div>
      </div>

      <dialog
        ref={dialogRef}
        className="mobile-nav"
        aria-labelledby={titleId}
        onClick={(event) => {
          if (event.target === dialogRef.current) closeNav()
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") closeNav()
        }}
        onClose={closeNav}
      >
        <div className="bg-background flex h-full flex-col">
          <div className="page-content flex h-16 items-center justify-between border-b">
            <p id={titleId} className="text-sm font-medium">
              Menu
            </p>
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label="Close menu"
              onClick={closeNav}
            >
              <X />
            </Button>
          </div>
          <nav className="page-content flex flex-1 flex-col gap-1 py-6">
            {NAV.map((item) => (
              <Link
                key={item.hash}
                to="/"
                hash={item.hash}
                className="hover:bg-muted rounded-lg px-3 py-3 text-base font-medium"
                onClick={() => {
                  track({ event: "nav_anchor", target: item.hash })
                  closeNav()
                }}
              >
                {item.label}
              </Link>
            ))}
            <div className="mt-6 flex flex-col gap-2">
              <Button variant="outline" size="lg" asChild>
                <Link
                  to="/login"
                  onClick={() => {
                    track({ event: "cta_login" })
                    closeNav()
                  }}
                >
                  Log in
                </Link>
              </Button>
              <Button size="lg" asChild>
                <Link
                  to="/signup"
                  onClick={() => {
                    track({ event: "cta_get_started", placement: "header" })
                    closeNav()
                  }}
                >
                  Get started for free
                </Link>
              </Button>
            </div>
          </nav>
        </div>
      </dialog>
    </header>
  )
}
