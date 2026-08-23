import { Link } from "@tanstack/react-router"

import { track } from "@/features/marketing/analytics"

export function LandingFooter() {
  const year = new Date().getFullYear()

  return (
    <footer>
      <div className="page-content flex flex-col gap-10 border-t py-12 sm:flex-row sm:items-start sm:justify-between">
        <p className="text-sm font-medium">Actionable AI</p>
        <div className="grid gap-10 sm:grid-cols-3 sm:gap-16">
          <div>
            <p className="text-sm font-medium">Product</p>
            <ul className="mt-4 flex flex-col gap-2">
              <li>
                <Link
                  to="/"
                  hash="how-it-works"
                  className="text-muted-foreground hover:text-foreground text-sm"
                  onClick={() =>
                    track({ event: "nav_anchor", target: "how-it-works" })
                  }
                >
                  How it works
                </Link>
              </li>
              <li>
                <Link
                  to="/"
                  hash="features"
                  className="text-muted-foreground hover:text-foreground text-sm"
                  onClick={() =>
                    track({ event: "nav_anchor", target: "features" })
                  }
                >
                  Features
                </Link>
              </li>
              <li>
                <Link
                  to="/"
                  hash="security"
                  className="text-muted-foreground hover:text-foreground text-sm"
                  onClick={() =>
                    track({ event: "nav_anchor", target: "security" })
                  }
                >
                  Security
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-medium">Legal</p>
            <ul className="mt-4 flex flex-col gap-2">
              <li>
                <Link
                  to="/terms"
                  className="text-muted-foreground hover:text-foreground text-sm"
                >
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link
                  to="/privacy"
                  className="text-muted-foreground hover:text-foreground text-sm"
                >
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-medium">Company</p>
            <ul className="mt-4 flex flex-col gap-2">
              <li>
                <a
                  href="mailto:hello@actionable.ai"
                  className="text-muted-foreground hover:text-foreground text-sm"
                >
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div className="page-content border-t py-6">
        <p className="text-muted-foreground text-sm">© {year} Actionable AI</p>
      </div>
    </footer>
  )
}
