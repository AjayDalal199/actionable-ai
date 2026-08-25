import { Link } from "@tanstack/react-router"

import { clearAccessToken, isLoggedIn } from "@/features/auth/session"
import { Button } from "@/shared/ui/button"

function goToLogin() {
  clearAccessToken()
  window.location.href = "/login"
}

export const NotFound = () => {
  return (
    <div
      className="flex min-h-screen items-center justify-center flex-col p-4"
      data-testid="not-found"
    >
      <div className="flex items-center z-10">
        <div className="flex flex-col ml-4 items-center justify-center p-4">
          <span className="text-6xl md:text-8xl font-bold leading-none mb-4">
            404
          </span>
          <span className="text-2xl font-bold mb-2">Oops!</span>
        </div>
      </div>

      <p className="text-lg text-muted-foreground mb-4 text-center z-10">
        The page you are looking for was not found.
      </p>
      <div className="z-10 flex gap-2">
        {isLoggedIn() ? (
          <Button className="mt-4" onClick={goToLogin}>
            Log out
          </Button>
        ) : (
          <Link to="/">
            <Button className="mt-4">Go home</Button>
          </Link>
        )}
      </div>
    </div>
  )
}
