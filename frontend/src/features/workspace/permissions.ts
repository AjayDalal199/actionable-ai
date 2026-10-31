import type { WorkspaceRole } from "@/api"

export function canEditWorkspace(
  role: WorkspaceRole | null | undefined,
): boolean {
  return role === "admin" || role === "editor"
}
