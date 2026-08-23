import { useAuth } from "@/features/auth/useAuth"

export function DashboardHome() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="max-w-sm truncate text-2xl">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Welcome back, nice to see you again!!!
        </p>
      </div>
    </div>
  )
}
