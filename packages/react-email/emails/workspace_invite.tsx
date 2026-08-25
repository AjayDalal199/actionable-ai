import { Text } from "@react-email/components"
import { LinkButton } from "../ui/Button"
import { Callout, Detail } from "../ui/Callout"
import { Heading } from "../ui/Heading"
import { Layout } from "../ui/Layout"
import { Link } from "../ui/Link"

type WorkspaceInviteProps = {
  project_name: string
  username: string
  workspace_name: string
  role: string
  link: string
}

export default function WorkspaceInvite({
  project_name = "{{ project_name }}",
  username = "{{ username }}",
  workspace_name = "{{ workspace_name }}",
  role = "{{ role }}",
  link = "{{ link }}",
}: WorkspaceInviteProps) {
  return (
    <Layout
      title={`${project_name} - Workspace invite`}
      preview={`You were added to ${workspace_name} on ${project_name}`}
      project_name={project_name}
    >
      <Heading>You've been added to a workspace</Heading>
      <Text className="text-[15px] leading-7 text-body">Hi {username},</Text>
      <Text className="text-[15px] leading-7 text-body">
        You now have access to {workspace_name} on {project_name}. Sign in to
        switch to it from the dashboard.
      </Text>
      <Callout>
        <Detail label="Workspace" value={workspace_name} />
        <Detail label="Role" value={role} />
      </Callout>
      <LinkButton href={link}>Open dashboard</LinkButton>
      <Text className="text-sm leading-6 text-muted">
        Or copy and paste this link into your browser:
        <br />
        <Link href={link}>{link}</Link>
      </Text>
      <Text className="text-sm leading-6 text-muted">
        If you weren't expecting this invite, you can safely ignore this email.
      </Text>
    </Layout>
  )
}
