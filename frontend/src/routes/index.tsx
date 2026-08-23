import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowRight,
  Bot,
  Building2,
  Check,
  ChevronDown,
  Code2,
  Copy,
  Database,
  ExternalLink,
  GitBranch,
  KeyRound,
  Lock,
  Menu,
  RefreshCw,
  Server,
  Shield,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from "lucide-react"
import { useEffect, useState } from "react"

import { Appearance } from "@/components/Common/Appearance"
import { ScrollReveal } from "@/components/Common/ScrollReveal"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

export const Route = createFileRoute("/")({
  component: LandingPage,
  head: () => ({
    meta: [
      {
        title: "Actionable AI — Turn Your API into an AI Agent",
      },
    ],
  }),
})

function LandingPage() {
  // Interactive Hero Widget State (HITL Simulation)
  const [heroActionStatus, setHeroActionStatus] = useState<
    "pending" | "confirmed" | "rejected"
  >("pending")

  // Pricing Billing Cycle State
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">(
    "annual",
  )

  // Code Snippet Active Tab State
  const [activeCodeTab, setActiveCodeTab] = useState<
    "schema" | "embed" | "fastapi"
  >("schema")
  const [copied, setCopied] = useState(false)

  // FAQ Accordion Active Item State
  const [openFaq, setOpenFaq] = useState<number | null>(0)

  // Active Navigation Section and Mobile Menu State
  const [activeSection, setActiveSection] = useState<string>("")
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = [
    { id: "features", label: "Features" },
    { id: "how-it-works", label: "How It Works" },
    { id: "code", label: "API & SDK" },
    { id: "security", label: "Security" },
    { id: "pricing", label: "Pricing" },
    { id: "faq", label: "FAQ" },
  ]

  useEffect(() => {
    const sectionIds = [
      "features",
      "how-it-works",
      "code",
      "security",
      "pricing",
      "faq",
    ]

    const visibleSections = new Map<string, number>()

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            visibleSections.set(entry.target.id, entry.intersectionRatio)
          } else {
            visibleSections.delete(entry.target.id)
          }
        }

        if (visibleSections.size > 0) {
          for (const id of sectionIds) {
            if (visibleSections.has(id)) {
              setActiveSection((prev) => (prev === id ? prev : id))
              break
            }
          }
        } else if (typeof window !== "undefined" && window.scrollY < 200) {
          setActiveSection((prev) => (prev === "" ? prev : ""))
        }
      },
      {
        rootMargin: "-80px 0px -40% 0px",
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    )

    for (const id of sectionIds) {
      const el = document.getElementById(id)
      if (el) {
        observer.observe(el)
      }
    }

    return () => observer.disconnect()
  }, [])

  const handleCopyCode = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const codeSnippets = {
    schema: `{
  "name": "delete_project",
  "description": "Permanently deletes a client staging or production environment.",
  "parameters": {
    "type": "object",
    "properties": {
      "project_id": { "type": "string", "description": "The unique project UUID" },
      "force": { "type": "boolean", "default": false }
    },
    "required": ["project_id"]
  },
  "requires_hitl": true,
  "risk_level": "critical"
}`,
    embed: `<!-- 1. Include the Actionable AI embed widget -->
<script 
  src="https://cdn.actionable.ai/v1/widget.js"
  data-project-id="proj_live_89f02c4"
  data-theme="dark"
  async
></script>

<!-- 2. Isolated Shadow DOM prevents CSS leaks from host application -->`,
    fastapi: `# Register an Actionable AI Tool in Python FastAPI
from fastapi import FastAPI
from actionable_ai import ActionTool, requires_hitl

app = FastAPI()

@app.post("/tools/rollback-deployment")
@requires_hitl(scope="admin:write")
async def rollback_deployment(cluster_id: str, commit_sha: str):
    """Executes a rollback after interactive human confirmation."""
    return {"status": "success", "cluster": cluster_id, "active_sha": commit_sha}`,
  }

  const faqs = [
    {
      q: "How does Human-in-the-Loop (HITL) security work?",
      a: "When the agent determines that an action matches a tool flagged with `requires_hitl: true` (such as deleting data, triggering billing events, or deploying code), the LangGraph orchestration engine pauses execution and sends an interactive confirmation card via Server-Sent Events (SSE). The action only executes once explicitly confirmed by the authorized human.",
    },
    {
      q: "How does A²I ingest our OpenAPI schemas and REST endpoints?",
      a: "You simply paste your OpenAPI 3.0/3.1 JSON/YAML specification or provide a Swagger URL. Our tool registry parses every endpoint, generates strict JSON schemas, and equips the LLM gateway with client-side and server-side execution capabilities.",
    },
    {
      q: "How does automated feature discovery & GitHub syncing work?",
      a: "You connect your GitHub or GitLab repository. Whenever updates are pushed to designated branches (e.g., develop or master), our background pipeline scans codebase changes, auto-generates technical documentation, and updates vector embeddings in PostgreSQL (pgvector) so your chatbot is never out of date.",
    },
    {
      q: "Will our proprietary source code or docs be used to train AI models?",
      a: "Never. Actionable AI enforces a strict zero-data-retention policy for foundation model training. All vector embeddings are isolated in multi-tenant or dedicated PostgreSQL schemas with AES-256 encryption at rest and TLS 1.3 in transit.",
    },
    {
      q: "How does the Shadow DOM embed widget ensure zero CSS conflicts?",
      a: "Our widget is built as a native Web Component encapsulated in the browser Shadow DOM. This isolates its stylesheets from the host application, guaranteeing that your site's CSS styles, resets, or font definitions will never break the chatbot UI.",
    },
    {
      q: "What happens if an end-user asks a question outside the chatbot's knowledge base?",
      a: "The system triggers an automated human handoff workflow, capturing the conversation transcript and user email, and routing it to your designated support email or webhook listener.",
    },
  ]

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-primary/20 selection:text-primary">
      {/* 1. Header / Navbar */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur-md transition-colors">
        <div className="w-full max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8 xl:px-12">
          {/* Left: Brand Logo & Title */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-primary text-primary-foreground font-bold shadow-xs transition-transform group-hover:scale-105">
                <Zap className="h-4 w-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold tracking-tight leading-tight">
                  Actionable AI
                </span>
                <span className="text-[10px] font-semibold text-muted-foreground tracking-wider uppercase">
                  A²I Platform
                </span>
              </div>
            </Link>
            <Badge
              variant="outline"
              className="hidden sm:inline-flex text-[11px] ml-2 border-primary/30 text-primary bg-primary/5"
            >
              MVP Phase 1
            </Badge>
          </div>

          {/* Right: Nav items to the right + Actions */}
          <div className="flex items-center gap-4 lg:gap-7">
            {/* Desktop Navigation Links aligned to the right */}
            <nav className="hidden md:flex items-center gap-5 lg:gap-6 text-sm font-medium">
              {navLinks.map((link) => {
                const isActive = activeSection === link.id
                return (
                  <a
                    key={link.id}
                    href={`#${link.id}`}
                    className={`relative py-1.5 transition-colors duration-200 ${
                      isActive
                        ? "text-primary font-semibold"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {link.label}
                    {isActive && (
                      <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full transition-all duration-300" />
                    )}
                  </a>
                )
              })}
            </nav>

            {/* Desktop Divider */}
            <div className="hidden md:block h-4 w-px bg-border" />

            {/* Actions */}
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="hidden sm:block">
                <Appearance />
              </div>
              <Link
                to="/login"
                className="hidden sm:inline-flex text-sm font-medium hover:text-primary transition-colors px-2 py-1"
              >
                Log in
              </Link>
              <Button
                asChild
                size="sm"
                className="hidden sm:inline-flex font-semibold shadow-xs"
              >
                <Link to="/signup">Get Started</Link>
              </Button>

              {/* Mobile Appearance Toggle */}
              <div className="sm:hidden flex items-center">
                <Appearance />
              </div>

              {/* Mobile Hamburger Menu Trigger */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden text-muted-foreground hover:text-foreground h-9 w-9"
                onClick={() => setMobileMenuOpen(true)}
                aria-label="Open Navigation Menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Sheet Drawer */}
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetContent
            side="right"
            className="w-[300px] sm:w-[360px] p-0 flex flex-col justify-between"
          >
            <div>
              <SheetHeader className="p-5 border-b border-border text-left">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded bg-primary text-primary-foreground font-bold shadow-xs">
                    <Zap className="h-4 w-4" />
                  </div>
                  <div className="flex flex-col">
                    <SheetTitle className="text-base font-bold tracking-tight leading-tight">
                      Actionable AI
                    </SheetTitle>
                    <SheetDescription className="text-[10px] font-semibold text-muted-foreground tracking-wider uppercase">
                      A²I Platform
                    </SheetDescription>
                  </div>
                </div>
              </SheetHeader>

              <div className="p-4 space-y-1">
                <p className="px-3 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Navigation
                </p>
                <nav className="flex flex-col gap-1">
                  {navLinks.map((link) => {
                    const isActive = activeSection === link.id
                    return (
                      <a
                        key={link.id}
                        href={`#${link.id}`}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center justify-between px-3.5 py-2.5 rounded-md text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary font-semibold"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        }`}
                      >
                        <span>{link.label}</span>
                        {isActive && (
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                        )}
                      </a>
                    )
                  })}
                </nav>
              </div>
            </div>

            <div className="p-5 border-t border-border bg-muted/20 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Appearance
                </span>
                <Appearance />
              </div>
              <div className="flex flex-col gap-2 pt-1">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="w-full justify-center"
                >
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                    Log in
                  </Link>
                </Button>
                <Button
                  asChild
                  size="sm"
                  className="w-full justify-center font-semibold shadow-xs"
                >
                  <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                    Get Started
                  </Link>
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </header>

      <main className="flex-1">
        {/* 2. Hero Section (Aligned with 01_Public_Marketing_Site.md) */}
        <section className="relative pt-16 pb-20 lg:pt-24 lg:pb-32 border-b bg-card/30">
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="max-w-4xl mx-auto text-center space-y-5">
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1 text-xs font-medium text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span className="text-foreground font-semibold">
                  Actionable Agent Platform
                </span>
                <span>•</span>
                <span>Strict Human-in-the-Loop Security</span>
              </div>

              {/* Exact Headline from 01_Public_Marketing_Site.md */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-balance">
                Turn your API into an{" "}
                <span className="text-primary">Actionable AI Agent.</span>
              </h1>

              {/* Exact Subheadline from 01_Public_Marketing_Site.md */}
              <p className="mx-auto max-w-2xl text-base sm:text-lg text-muted-foreground text-balance leading-relaxed">
                Embed a fully autonomous, RAG-powered AI assistant into your
                product in minutes. Built for the enterprise with strict
                Human-in-the-Loop security guarantees.
              </p>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-3">
                <Button
                  size="lg"
                  asChild
                  className="h-11 px-7 text-sm font-semibold w-full sm:w-auto shadow-xs"
                >
                  <Link to="/signup">
                    Get Started <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  asChild
                  className="h-11 px-7 text-sm font-medium w-full sm:w-auto"
                >
                  <a href="#code">View Documentation</a>
                </Button>
              </div>

              <div className="pt-3 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-primary" /> Instant OpenAPI
                  / Swagger Import
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-primary" /> Zero CSS Leaks
                  (Shadow DOM)
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-primary" /> PostgreSQL
                  pgvector RAG
                </span>
              </div>
            </ScrollReveal>

            {/* Split Screen Visual (As specified in 01_Public_Marketing_Site.md) */}
            <ScrollReveal className="mt-14 mx-auto max-w-6xl w-full rounded-lg border border-border bg-card shadow-sm overflow-hidden">
              {/* Mock Window Header */}
              <div className="flex items-center justify-between border-b bg-muted/40 px-4 py-2.5 text-xs text-muted-foreground font-mono">
                <div className="flex items-center gap-2">
                  <div className="h-2.5 w-2.5 rounded-full bg-border" />
                  <div className="h-2.5 w-2.5 rounded-full bg-border" />
                  <div className="h-2.5 w-2.5 rounded-full bg-border" />
                  <span className="ml-2 font-medium text-foreground">
                    Actionable AI Split Engine: Schema on Left, Widget Execution
                    on Right
                  </span>
                </div>
                <Badge
                  variant="outline"
                  className="text-[10px] text-primary border-primary/30"
                >
                  LangGraph HITL State
                </Badge>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x border-border">
                {/* Left: JSON API Schema Definition */}
                <div className="lg:col-span-5 p-5 bg-card flex flex-col justify-between font-mono text-xs">
                  <div>
                    <div className="flex items-center justify-between pb-3 mb-3 border-b border-border">
                      <span className="font-semibold text-foreground flex items-center gap-1.5">
                        <Code2 className="h-4 w-4 text-primary" /> Registered
                        Tool Schema
                      </span>
                      <Badge variant="secondary" className="text-[10px]">
                        OpenAPI 3.1
                      </Badge>
                    </div>
                    <pre className="text-muted-foreground text-[11px] leading-relaxed overflow-x-auto">
                      <code>{`{
  "name": "delete_project",
  "description": "Deletes staging instance",
  "parameters": {
    "project_id": "staging-node-04"
  },
  "requires_hitl": true,
  "risk_level": "critical"
}`}</code>
                    </pre>
                  </div>

                  <div className="pt-4 border-t border-border mt-4 text-[11px] text-muted-foreground">
                    <p className="text-foreground font-medium">
                      Policy Engine Status:
                    </p>
                    <p className="text-amber-500 font-semibold mt-0.5">
                      ⚠️ Tool flagged for mandatory user authorization
                    </p>
                  </div>
                </div>

                {/* Right: Chatbot Widget executing action with HITL */}
                <div className="lg:col-span-7 p-5 bg-background flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-2 text-xs">
                      <span className="font-semibold text-foreground flex items-center gap-1.5">
                        <Bot className="h-4 w-4 text-primary" /> Embedded
                        Chatbot Widget
                      </span>
                      <span className="text-[11px] text-emerald-500 font-medium">
                        ● SSE Stream Ready
                      </span>
                    </div>

                    {/* User Prompt */}
                    <div className="flex items-start gap-2 max-w-[85%] ml-auto justify-end">
                      <div className="rounded bg-primary px-3.5 py-2 text-xs text-primary-foreground font-medium">
                        Can you delete the staging project `staging-node-04`?
                      </div>
                    </div>

                    {/* AI Bubble & HITL Confirmation Card */}
                    <div className="flex items-start gap-2.5 max-w-[95%]">
                      <div className="h-6 w-6 rounded bg-primary/20 text-primary flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="h-3.5 w-3.5" />
                      </div>
                      <div className="space-y-2.5 w-full">
                        <p className="text-xs text-muted-foreground">
                          I located the project{" "}
                          <code className="text-foreground font-mono font-semibold">
                            staging-node-04
                          </code>
                          . Because this action is destructive, confirmation is
                          required:
                        </p>

                        {/* HITL Card styled according to Enterprise Design System */}
                        <div className="rounded border border-destructive/60 bg-card p-3.5 space-y-2.5 text-xs shadow-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-destructive flex items-center gap-1.5">
                              <Shield className="h-3.5 w-3.5" /> Action
                              Confirmation Required
                            </span>
                            <Badge
                              variant="outline"
                              className="text-[10px] text-destructive border-destructive/40 bg-destructive/10"
                            >
                              Critical Action
                            </Badge>
                          </div>

                          <div className="p-2 rounded bg-background border border-border font-mono text-[11px] text-muted-foreground">
                            POST /v1/projects/staging-node-04/delete
                          </div>

                          {heroActionStatus === "pending" && (
                            <div className="flex items-center gap-2 pt-1">
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                onClick={() => setHeroActionStatus("rejected")}
                              >
                                Cancel
                              </Button>
                              <Button
                                size="sm"
                                className="h-7 text-xs font-semibold"
                                onClick={() => setHeroActionStatus("confirmed")}
                              >
                                Confirm Action
                              </Button>
                            </div>
                          )}

                          {heroActionStatus === "confirmed" && (
                            <div className="flex items-center gap-2 text-xs text-emerald-500 font-medium pt-1">
                              <Check className="h-4 w-4" />
                              <span>
                                Action approved. Staging environment deleted
                                successfully.
                              </span>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 text-[10px] ml-auto"
                                onClick={() => setHeroActionStatus("pending")}
                              >
                                Reset
                              </Button>
                            </div>
                          )}

                          {heroActionStatus === "rejected" && (
                            <div className="flex items-center gap-2 text-xs text-destructive font-medium pt-1">
                              <span>
                                Action aborted. Execution halted by user.
                              </span>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 text-[10px] ml-auto"
                                onClick={() => setHeroActionStatus("pending")}
                              >
                                Reset
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-2 border-t border-border flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                    <span>Session: JWT Signed</span>
                    <span>State: LangGraph Paused</span>
                  </div>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* 3. Core 4 Value Propositions (Directly from 01_Public_Marketing_Site.md) */}
        <section id="features" className="py-20 lg:py-28 border-b scroll-mt-20">
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-16 space-y-3">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Core Capabilities
              </Badge>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
                Enterprise AI Built for Real Execution
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Move beyond toy conversational chatbots. A²I connects your data
                and tools with strict security guarantees.
              </p>
            </ScrollReveal>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* 1. Bring Your Own APIs */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Server className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Bring Your Own APIs
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Simply paste your OpenAPI specs or JSON schemas. Our
                    platform automatically maps them to LLM tools for client and
                    server execution.
                  </p>
                </div>
                <div className="pt-4 border-t border-border text-[11px] font-mono text-primary">
                  OpenAPI 3.0/3.1 Native
                </div>
              </ScrollReveal>

              {/* 2. Instant RAG */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Database className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Instant RAG
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Drag and drop your company policies or PDF manuals. Your
                    agent learns your business context instantly with PostgreSQL
                    pgvector.
                  </p>
                </div>
                <div className="pt-4 border-t border-border text-[11px] font-mono text-primary">
                  pgvector Vector Indexing
                </div>
              </ScrollReveal>

              {/* 3. Human-in-the-Loop (HITL) Security */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Human-in-the-Loop (HITL)
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Never worry about rogue AI. Flag destructive endpoints (like
                    DELETE or billing) to force an interactive human
                    confirmation card before execution.
                  </p>
                </div>
                <div className="pt-4 border-t border-border text-[11px] font-mono text-primary">
                  LangGraph State Pause
                </div>
              </ScrollReveal>

              {/* 4. Embeddable Shadow DOM Widget */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-3 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Code2 className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Shadow DOM Widget
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Drop one script tag into your codebase. Our widget is
                    perfectly isolated from your CSS, ensuring a flawless UI
                    every time.
                  </p>
                </div>
                <div className="pt-4 border-t border-border text-[11px] font-mono text-primary">
                  Zero CSS Pollution
                </div>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 4. Additional Capabilities from PRD & Architecture */}
        <section className="py-20 lg:py-28 bg-card/30 border-b">
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-16 space-y-3">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Full Lifecycle Support
              </Badge>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
                Designed for Developers & Product Teams
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Automated codebase documentation, continuous GitHub syncing, and
                dual technical/customer doc pipelines.
              </p>
            </ScrollReveal>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* GitHub Auto-Sync */}
              <ScrollReveal className="p-6 rounded-lg border border-border bg-card space-y-3">
                <div className="h-9 w-9 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                  <GitBranch className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Continuous GitHub Auto-Documentation
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Connect code repositories. Webhook listeners trigger automated
                  feature discovery and re-index vector representations whenever
                  code is pushed.
                </p>
              </ScrollReveal>

              {/* Dual Documentation */}
              <ScrollReveal className="p-6 rounded-lg border border-border bg-card space-y-3">
                <div className="h-9 w-9 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                  <RefreshCw className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Dual Technical & Customer Docs
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Maintains distinct architectural references for engineers and
                  clean knowledge base articles for customer chatbot
                  interactions.
                </p>
              </ScrollReveal>

              {/* Multi-Tenant RBAC */}
              <ScrollReveal className="p-6 rounded-lg border border-border bg-card space-y-3">
                <div className="h-9 w-9 rounded bg-primary/10 text-primary flex items-center justify-center font-bold">
                  <Users className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Multi-Tenant RBAC & Signed JWTs
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Enforce strict Admin, Editor, and Viewer roles with signed JWT
                  authorization ensuring callers only execute authorized
                  actions.
                </p>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 5. How It Works (Step-by-Step) */}
        <section
          id="how-it-works"
          className="py-20 lg:py-28 border-b scroll-mt-20"
        >
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-16 space-y-3">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Simple 3-Step Setup
              </Badge>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
                How Actionable AI Works
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Set up your action-capable agent in three simple steps.
              </p>
            </ScrollReveal>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-primary font-mono bg-primary/10 px-2 py-1 rounded">
                    STEP 01
                  </span>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Connect Docs & OpenAPI
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Upload PDFs, link GitHub repos, or register your REST API
                  endpoints. The system parses schemas and vectorizes
                  documentation in pgvector.
                </p>
              </ScrollReveal>

              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-primary font-mono bg-primary/10 px-2 py-1 rounded">
                    STEP 02
                  </span>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Configure HITL Security
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Classify endpoints as Read-Only or Write. Flag dangerous tools
                  with mandatory Human-in-the-Loop verification policies.
                </p>
              </ScrollReveal>

              <ScrollReveal className="rounded-lg border border-border bg-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-primary font-mono bg-primary/10 px-2 py-1 rounded">
                    STEP 03
                  </span>
                  <Code2 className="h-4 w-4 text-muted-foreground" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Embed Widget or Call API
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Drop a single script tag into your website. The isolated
                  Shadow DOM widget streams answers and renders interactive
                  action confirmation cards.
                </p>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 6. Code & SDK Integration */}
        <section
          id="code"
          className="py-20 lg:py-28 bg-card/30 border-b scroll-mt-20"
        >
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
              <ScrollReveal className="lg:col-span-5 space-y-5">
                <Badge
                  variant="outline"
                  className="text-xs text-primary border-primary/30 bg-primary/5"
                >
                  Developer First
                </Badge>
                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
                  Seamless Integration for Any Stack
                </h2>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  Whether embedding a lightweight widget on your web app or
                  registering custom backend tool endpoints in FastAPI,
                  integration takes only a few lines of code.
                </p>

                <div className="space-y-2.5 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-primary" />
                    <span>
                      Single script tag embed with Shadow DOM isolation
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-primary" />
                    <span>
                      FastAPI & Python SDK decorators (`@requires_hitl`)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-primary" />
                    <span>
                      Streaming SSE events for tokens and interactive action
                      cards
                    </span>
                  </div>
                </div>

                <div className="pt-2">
                  <Button asChild variant="outline" size="sm">
                    <Link to="/signup">
                      Explore SDK Documentation{" "}
                      <ExternalLink className="ml-2 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                </div>
              </ScrollReveal>

              <ScrollReveal className="lg:col-span-7">
                <div className="rounded-lg border border-border bg-card shadow-xs overflow-hidden">
                  <div className="flex items-center justify-between border-b border-border bg-muted/40 px-4">
                    <div className="flex gap-1 py-2">
                      <button
                        type="button"
                        onClick={() => setActiveCodeTab("schema")}
                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                          activeCodeTab === "schema"
                            ? "bg-background text-foreground shadow-xs"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        JSON Schema Tool
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveCodeTab("embed")}
                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                          activeCodeTab === "embed"
                            ? "bg-background text-foreground shadow-xs"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        Widget Embed Code
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveCodeTab("fastapi")}
                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                          activeCodeTab === "fastapi"
                            ? "bg-background text-foreground shadow-xs"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        FastAPI Tool Hook
                      </button>
                    </div>

                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() =>
                        handleCopyCode(codeSnippets[activeCodeTab])
                      }
                      title="Copy snippet"
                    >
                      {copied ? (
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>

                  <div className="p-4 bg-background font-mono text-xs leading-relaxed overflow-x-auto text-foreground">
                    <pre>
                      <code>{codeSnippets[activeCodeTab]}</code>
                    </pre>
                  </div>
                </div>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 7. Security & Privacy Section */}
        <section id="security" className="py-20 lg:py-28 border-b scroll-mt-20">
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-16 space-y-3">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Enterprise Trust
              </Badge>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
                Enterprise Security & Data Isolation
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Strict data boundaries and compliance controls to safeguard
                enterprise knowledge.
              </p>
            </ScrollReveal>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <ScrollReveal className="p-5 rounded-lg border border-border bg-card space-y-2.5">
                <Lock className="h-5 w-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">
                  Zero Model Training
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Your documentation, API keys, and code snippets are never
                  shared or used to train foundational AI models.
                </p>
              </ScrollReveal>

              <ScrollReveal className="p-5 rounded-lg border border-border bg-card space-y-2.5">
                <ShieldCheck className="h-5 w-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">
                  AES-256 Encryption
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Encrypted storage at rest and TLS 1.3 in transit across all
                  vector databases and API integrations.
                </p>
              </ScrollReveal>

              <ScrollReveal className="p-5 rounded-lg border border-border bg-card space-y-2.5">
                <KeyRound className="h-5 w-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">
                  Signed JWT Authentication
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Widgets require signed authorization tokens to prevent
                  unauthorized tool execution and prompt injection.
                </p>
              </ScrollReveal>

              <ScrollReveal className="p-5 rounded-lg border border-border bg-card space-y-2.5">
                <Building2 className="h-5 w-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">
                  SOC2 & GDPR Readiness
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Tamper-evident audit logging, granular workspace RBAC, and
                  configurable data retention policies.
                </p>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 8. Pricing Section */}
        <section
          id="pricing"
          className="py-20 lg:py-28 bg-card/30 border-b scroll-mt-20"
        >
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-12 space-y-3">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Simple Pricing
              </Badge>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
                Predictable Plans for Every Stage
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Start with our Free tier for testing and upgrade to Growth as
                your team scales.
              </p>

              {/* Billing Toggle */}
              <div className="flex items-center justify-center gap-3 pt-3">
                <span
                  className={`text-xs font-medium ${billingCycle === "monthly" ? "text-foreground font-semibold" : "text-muted-foreground"}`}
                >
                  Monthly
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setBillingCycle(
                      billingCycle === "monthly" ? "annual" : "monthly",
                    )
                  }
                  className="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border border-border bg-primary transition-colors focus-visible:outline-none"
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-primary-foreground shadow-sm transition duration-150 ${
                      billingCycle === "annual"
                        ? "translate-x-5"
                        : "translate-x-0.5"
                    }`}
                  />
                </button>
                <span
                  className={`text-xs font-medium flex items-center gap-1.5 ${billingCycle === "annual" ? "text-foreground font-semibold" : "text-muted-foreground"}`}
                >
                  Annual
                  <Badge
                    variant="secondary"
                    className="text-[10px] bg-primary/10 text-primary border-primary/20 py-0"
                  >
                    Save 20%
                  </Badge>
                </span>
              </div>
            </ScrollReveal>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 max-w-6xl mx-auto">
              {/* Starter */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 flex flex-col justify-between shadow-xs">
                <div className="space-y-5">
                  <div>
                    <h3 className="text-base font-bold text-foreground">
                      Starter (MVP)
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Free for side projects, documentation testing, and MVPs.
                    </p>
                  </div>

                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-foreground">
                      $0
                    </span>
                    <span className="text-xs text-muted-foreground">
                      / month
                    </span>
                  </div>

                  <div className="space-y-2.5 pt-3 border-t border-border text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>1,000 queries / month</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>3 Manual Document Uploads (PDF/Markdown)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Standard Shadow DOM Widget</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>pgvector semantic search</span>
                    </div>
                  </div>
                </div>

                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="w-full mt-6"
                >
                  <Link to="/signup">Get Started for Free</Link>
                </Button>
              </ScrollReveal>

              {/* Growth */}
              <ScrollReveal className="rounded-lg border-2 border-primary bg-card p-6 flex flex-col justify-between shadow-md relative">
                <Badge className="absolute -top-2.5 right-6 bg-primary text-primary-foreground text-[10px]">
                  Most Popular
                </Badge>

                <div className="space-y-5">
                  <div>
                    <h3 className="text-base font-bold text-foreground">
                      Growth (V1)
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      For production SaaS applications and technical teams.
                    </p>
                  </div>

                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-foreground">
                      ${billingCycle === "annual" ? "39" : "49"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      / month
                    </span>
                  </div>

                  <div className="space-y-2.5 pt-3 border-t border-border text-xs text-foreground">
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>25,000 queries / month</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Continuous GitHub Codebase Sync</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Full Human-in-the-Loop (HITL) Workflows</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Automated Feature Discovery Pipeline</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Custom OpenAPI Tool Registration</span>
                    </div>
                  </div>
                </div>

                <Button
                  asChild
                  size="sm"
                  className="w-full mt-6 font-semibold shadow-xs"
                >
                  <Link to="/signup">Start 14-Day Free Trial</Link>
                </Button>
              </ScrollReveal>

              {/* Enterprise */}
              <ScrollReveal className="rounded-lg border border-border bg-card p-6 flex flex-col justify-between shadow-xs">
                <div className="space-y-5">
                  <div>
                    <h3 className="text-base font-bold text-foreground">
                      Enterprise
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      For organizations requiring dedicated infrastructure and
                      custom SLAs.
                    </p>
                  </div>

                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-foreground">
                      Custom
                    </span>
                  </div>

                  <div className="space-y-2.5 pt-3 border-t border-border text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Unlimited queries & custom rate limits</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Dedicated PostgreSQL pgvector cluster</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>Custom LLM Gateway (On-Prem / Private VPC)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span>SAML 2.0 / SSO & Dedicated Support Engineer</span>
                    </div>
                  </div>
                </div>

                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="w-full mt-6"
                >
                  <Link to="/signup">Contact Sales</Link>
                </Button>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* 9. FAQ Section */}
        <section id="faq" className="py-20 lg:py-28 border-b scroll-mt-20">
          <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="text-center space-y-3 mb-12">
              <Badge
                variant="outline"
                className="text-xs text-primary border-primary/30 bg-primary/5"
              >
                Questions & Answers
              </Badge>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
                Frequently Asked Questions
              </h2>
            </ScrollReveal>

            <div className="space-y-3">
              {faqs.map((faq, idx) => {
                const isOpen = openFaq === idx
                return (
                  <ScrollReveal
                    key={faq.q}
                    className="rounded-lg border border-border bg-card overflow-hidden transition-colors"
                  >
                    <button
                      type="button"
                      onClick={() => setOpenFaq(isOpen ? null : idx)}
                      className="flex w-full items-center justify-between p-4 text-left text-sm font-semibold hover:text-primary transition-colors gap-4"
                    >
                      <span>{faq.q}</span>
                      <ChevronDown
                        className={`h-4 w-4 shrink-0 transition-transform duration-200 ${
                          isOpen
                            ? "rotate-180 text-primary"
                            : "text-muted-foreground"
                        }`}
                      />
                    </button>
                    {isOpen && (
                      <div className="px-4 pb-4 text-xs text-muted-foreground leading-relaxed border-t border-border bg-muted/10 pt-3">
                        {faq.a}
                      </div>
                    )}
                  </ScrollReveal>
                )
              })}
            </div>
          </div>
        </section>

        {/* 10. Final CTA Section */}
        <section className="py-16 lg:py-24 bg-card/40">
          <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
            <ScrollReveal className="rounded-xl border border-border bg-card p-8 sm:p-14 text-center max-w-5xl mx-auto space-y-5 shadow-xs">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-balance">
                Ready to Turn Your API into an{" "}
                <span className="text-primary">Actionable AI Agent?</span>
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground max-w-xl mx-auto text-balance leading-relaxed">
                Connect your documentation and OpenAPI schemas to embed a
                secure, Human-in-the-Loop verified AI assistant into your
                product today.
              </p>

              <div className="pt-2 flex flex-col sm:flex-row justify-center items-center gap-3">
                <Button
                  size="lg"
                  asChild
                  className="h-10 px-6 text-sm font-semibold shadow-xs w-full sm:w-auto"
                >
                  <Link to="/signup">
                    Get Started for Free <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  asChild
                  className="h-10 px-6 text-sm font-medium w-full sm:w-auto"
                >
                  <Link to="/login">Sign In to Dashboard</Link>
                </Button>
              </div>

              <p className="text-[11px] text-muted-foreground pt-1">
                No credit card required • Instant OpenAPI schema import • Full
                HITL security
              </p>
            </ScrollReveal>
          </div>
        </section>
      </main>

      {/* 11. Footer (Matches 01_Public_Marketing_Site.md) */}
      <footer className="border-t bg-card py-12 sm:py-16 text-muted-foreground text-xs">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 xl:px-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div className="col-span-2 space-y-3">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground">
                  <Zap className="h-3.5 w-3.5" />
                </div>
                <span className="text-sm font-bold text-foreground tracking-tight">
                  Actionable AI (A²I)
                </span>
              </div>
              <p className="max-w-sm text-xs leading-relaxed">
                The general-purpose chatbot integration platform enabling
                companies to easily embed an intelligent, agentic AI assistant
                with strict Human-in-the-Loop safeguards.
              </p>
            </div>

            <div className="space-y-2.5">
              <p className="font-semibold text-foreground text-xs uppercase tracking-wider">
                Product
              </p>
              <ul className="space-y-1.5">
                <li>
                  <a
                    href="#features"
                    className="hover:text-primary transition-colors"
                  >
                    Bring Your Own APIs
                  </a>
                </li>
                <li>
                  <a
                    href="#features"
                    className="hover:text-primary transition-colors"
                  >
                    Instant RAG (pgvector)
                  </a>
                </li>
                <li>
                  <a
                    href="#features"
                    className="hover:text-primary transition-colors"
                  >
                    Human-in-the-Loop (HITL)
                  </a>
                </li>
                <li>
                  <a
                    href="#features"
                    className="hover:text-primary transition-colors"
                  >
                    Shadow DOM Widget
                  </a>
                </li>
                <li>
                  <Link
                    to="/dashboard"
                    className="hover:text-primary transition-colors"
                  >
                    B2B Dashboard
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-2.5">
              <p className="font-semibold text-foreground text-xs uppercase tracking-wider">
                Legal & Company
              </p>
              <ul className="space-y-1.5">
                <li>
                  <a
                    href="#pricing"
                    className="hover:text-primary transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <Link to="/" className="hover:text-primary transition-colors">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link to="/" className="hover:text-primary transition-colors">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link
                    to="/signup"
                    className="hover:text-primary transition-colors"
                  >
                    Contact Sales
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px]">
            <p>
              © {new Date().getFullYear()} Actionable AI (A²I) Platform. All
              rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="#pricing"
                className="hover:text-primary transition-colors"
              >
                Pricing
              </a>
              <Link to="/" className="hover:text-primary transition-colors">
                Terms
              </Link>
              <Link to="/" className="hover:text-primary transition-colors">
                Privacy
              </Link>
              <Link
                to="/signup"
                className="hover:text-primary transition-colors"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
