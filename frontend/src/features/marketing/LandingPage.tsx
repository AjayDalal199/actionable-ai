import { Link } from "@tanstack/react-router"
import { ChevronDown } from "lucide-react"
import { type ReactNode, useEffect, useId, useState } from "react"

import { track } from "@/features/marketing/analytics"
import {
  FileListArtifact,
  HitlCard,
  SchemaArtifact,
  ScriptArtifact,
  WidgetMock,
} from "@/features/marketing/artifacts"
import { LandingFooter } from "@/features/marketing/LandingFooter"
import { LandingHeader } from "@/features/marketing/LandingHeader"
import { Button } from "@/shared/ui/button"

const PROOF = [
  {
    fact: "Under 5 minutes",
    label: "Upload docs, register a tool, copy one script tag",
  },
  {
    fact: "Confirm before it happens",
    label: "They confirm the action. Then the agent does it.",
  },
  {
    fact: "Isolated widget",
    label: "Your CSS stays out. Ours stays in.",
  },
] as const

const PROBLEMS = [
  {
    title: "Stale knowledge",
    body: "The bot answers from a wiki that last matched the product two releases ago.",
  },
  {
    title: "Passive answers",
    body: "“Go to Settings → Billing → Cancel” is not help. It is a reading assignment.",
  },
  {
    title: "Unsafe agents",
    body: "An agent that can act without a confirmation gate is how refunds and deletes escape into production.",
  },
] as const

const STEPS = [
  {
    n: "01",
    title: "Feed it what you already have",
    body: "Drop PDFs, Markdown, or pasted docs. The agent retrieves from that corpus immediately.",
    artifact: <FileListArtifact />,
  },
  {
    n: "02",
    title: "Register the actions",
    body: "Point at OpenAPI, a schema, or a function. Writes ask the user to confirm the action first.",
    artifact: <SchemaArtifact />,
  },
  {
    n: "03",
    title: "Drop the widget",
    body: "One script tag, Shadow DOM, signed user context. The same agent is now in their product.",
    artifact: <ScriptArtifact />,
  },
] as const

const SECURITY_POINTS = [
  {
    title: "Signed user context",
    body: "Every session carries a signed user token.",
  },
  {
    title: "Read vs write",
    body: "Tools are classified before they can run.",
  },
  {
    title: "Confirm the action",
    body: "They confirm what will happen, in plain language. They never see the API.",
  },
  {
    title: "Go back means abort",
    body: "Go back aborts. The agent does not retry quietly.",
  },
] as const

const AUDIENCES = [
  {
    title: "Engineering",
    body: "Ship an agent surface without a custom orchestration project. You wire the APIs; their customers never see them.",
  },
  {
    title: "Product / docs",
    body: "Put current manuals in front of the agent and keep customer-facing wording accurate.",
  },
  {
    title: "Their end-users",
    body: "Ask in the product and get the task offered, not a tour of the settings tree.",
  },
] as const

const COMPARE = [
  {
    row: "“How do I export?”",
    left: "A link to an article",
    right: "Offer to export, then do it",
  },
  {
    row: "Knowledge",
    left: "Static help-center articles",
    right: "The docs you uploaded",
  },
  {
    row: "Writes",
    left: "None, or hidden automations",
    right: "They confirm the action first",
  },
  {
    row: "Install",
    left: "Another chat bubble",
    right: "One isolated script",
  },
] as const

const FAQ_ITEMS: { q: string; a: ReactNode }[] = [
  {
    q: "Do I need to connect GitHub to try this?",
    a: "No. Upload documents and register tools by hand. Repository sync is a later path, not the front door.",
  },
  {
    q: "What happens if the agent wants to delete or charge?",
    a: "That is a write. The widget asks them to confirm the action in plain language. Confirm does it. Go back does not. They never see an API.",
  },
  {
    q: "Will this restyle our app?",
    a: "The widget runs in Shadow DOM. Host CSS stays out; widget CSS stays in.",
  },
  {
    q: "Is there a free tier?",
    a: "Yes. Create an account, ingest a small corpus, and embed the widget. Paid limits and automation come after you have a working agent.",
  },
  {
    q: "Where does user data go?",
    a: (
      <>
        Chat and tool calls run through our backend so the model can retrieve
        and act. You authorize actions with a signed user context. Full
        data-processing terms live in the{" "}
        <Link
          to="/privacy"
          className="text-primary underline-offset-4 hover:underline"
        >
          Privacy Policy
        </Link>
        .
      </>
    ),
  },
  {
    q: "Can we talk to sales?",
    a: (
      <>
        For volume, SSO, or a security review, use{" "}
        <a
          href="mailto:hello@actionable.ai"
          className="text-primary underline-offset-4 hover:underline"
        >
          Contact
        </a>
        . The default path is self-serve signup.
      </>
    ),
  },
]

export function LandingPage() {
  useEffect(() => {
    track({ event: "landing_view" })
  }, [])

  return (
    <div className="flex min-h-svh flex-col">
      <a href="#hero-heading" className="skip-link">
        Skip to content
      </a>
      <LandingHeader />
      <main>
        <Hero />
        <ProofStrip />
        <Problem />
        <HowItWorks />
        <Features />
        <Security />
        <Audiences />
        <Compare />
        <Faq />
        <ClosingCta />
      </main>
      <LandingFooter />
    </div>
  )
}

function SectionHeading({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string
  title: string
  children?: ReactNode
}) {
  return (
    <header className="mb-12 max-w-2xl">
      {eyebrow ? (
        <p className="text-primary mb-3 text-[13px] font-medium tracking-wide">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="text-section">{title}</h2>
      {children ? (
        <p className="text-muted-foreground mt-4 text-lg leading-relaxed">
          {children}
        </p>
      ) : null}
    </header>
  )
}

function Hero() {
  return (
    <section className="page-content grid items-start gap-12 py-16 lg:grid-cols-[minmax(0,1fr)_360px] lg:gap-20 lg:py-24">
      <div>
        <p className="text-primary text-[13px] font-medium tracking-wide">
          Agent infrastructure for SaaS products
        </p>
        <h1 id="hero-heading" className="text-display mt-5">
          Give your product an agent that can actually do things.
        </h1>
        <p className="text-muted-foreground mt-6 max-w-lg text-lg leading-relaxed">
          Embed a widget that answers from your docs, does the work in your
          product, and asks before anything that cannot be undone. Live in
          minutes, not a quarter.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button size="lg" asChild>
            <Link
              to="/signup"
              onClick={() =>
                track({ event: "cta_get_started", placement: "hero" })
              }
            >
              Get started for free
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link
              to="/"
              hash="how-it-works"
              onClick={() =>
                track({ event: "nav_anchor", target: "how-it-works" })
              }
            >
              See how it works
            </Link>
          </Button>
        </div>
      </div>
      <div className="flex justify-center lg:justify-end">
        <WidgetMock />
      </div>
    </section>
  )
}

function ProofStrip() {
  return (
    <section>
      <ul className="page-content grid border-t sm:grid-cols-3">
        {PROOF.map((item, index) => (
          <li
            key={item.fact}
            className={
              index > 0
                ? "border-t py-8 sm:border-t-0 sm:border-l sm:px-10 sm:py-9"
                : "py-8 sm:py-9 sm:pr-10"
            }
          >
            <p className="font-semibold">{item.fact}</p>
            <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
              {item.label}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}

function Problem() {
  return (
    <section className="page-section page-content">
      <SectionHeading title="Most in-product chat still leaves the user to finish the job." />
      <ul className="grid gap-10 md:grid-cols-3 md:gap-12">
        {PROBLEMS.map((item) => (
          <li key={item.title}>
            <h3 className="text-base font-semibold">{item.title}</h3>
            <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
              {item.body}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}

function HowItWorks() {
  return (
    <section id="how-it-works" className="page-section page-content">
      <SectionHeading
        eyebrow="How it works"
        title="Three steps. Then it lives in your app."
      />
      <ol className="grid gap-12 lg:grid-cols-3 lg:gap-10">
        {STEPS.map((step) => (
          <li key={step.n} className="flex flex-col">
            <span className="text-primary font-mono text-sm">{step.n}</span>
            <h3 className="mt-4 text-lg font-semibold">{step.title}</h3>
            <p className="text-muted-foreground mt-3 mb-6 flex-1 text-sm leading-relaxed">
              {step.body}
            </p>
            {step.artifact}
          </li>
        ))}
      </ol>
    </section>
  )
}

function Features() {
  const items = [
    {
      title: "They confirm the action",
      body: "Writes show what will happen, in plain language. They confirm or go back. They never see an API.",
      artifact: <HitlCard />,
    },
    {
      title: "Knowledge in minutes",
      body: "Upload policies, manuals, and product docs. Retrieval is the default path for questions that should not become an action.",
      artifact: <FileListArtifact />,
    },
    {
      title: "Bring your own APIs",
      body: "Paste OpenAPI or a JSON schema. You keep the APIs. The agent gets a typed contract. Their customers never see a request.",
      artifact: <SchemaArtifact />,
    },
    {
      title: "A widget that will not fight your CSS",
      body: "Shadow DOM isolation, small payload, XSS sanitization. Built so an engineer can ship it without a design-system collision.",
      artifact: <ScriptArtifact />,
    },
  ] as const

  return (
    <section id="features" className="page-section page-content">
      <SectionHeading eyebrow="Features" title="Built to act, with a brake." />
      <ul className="grid gap-x-12 gap-y-14 md:grid-cols-2">
        {items.map((item) => (
          <li key={item.title} className="flex flex-col">
            <h3 className="text-lg font-semibold">{item.title}</h3>
            <p className="text-muted-foreground mt-3 mb-6 flex-1 text-sm leading-relaxed">
              {item.body}
            </p>
            {item.artifact}
          </li>
        ))}
      </ul>
    </section>
  )
}

function Security() {
  return (
    <section id="security" className="page-section page-content">
      <div className="grid items-start gap-12 lg:grid-cols-2 lg:gap-20">
        <div>
          <SectionHeading
            eyebrow="Security"
            title="The agent does not get a blank check."
          >
            Your backend remains the source of authorization. The platform does
            not invent permissions.
          </SectionHeading>
          <ul className="flex flex-col gap-6">
            {SECURITY_POINTS.map((item) => (
              <li key={item.title}>
                <h3 className="text-sm font-semibold">{item.title}</h3>
                <p className="text-muted-foreground mt-1 text-sm leading-relaxed">
                  {item.body}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div className="lg:pt-10">
          <HitlCard />
          <p className="text-muted-foreground mt-4 text-sm leading-relaxed">
            What they see: the action, the consequence, a choice. No endpoint.
          </p>
        </div>
      </div>
    </section>
  )
}

function Audiences() {
  return (
    <section className="page-section page-content">
      <SectionHeading title="One platform, three jobs." />
      <ul className="grid gap-10 md:grid-cols-3 md:gap-12">
        {AUDIENCES.map((item) => (
          <li key={item.title}>
            <h3 className="text-base font-semibold">{item.title}</h3>
            <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
              {item.body}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}

function Compare() {
  return (
    <section className="page-section page-content">
      <SectionHeading title="A help-center bot vs an agent that does the work." />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="w-[28%] py-3 pr-6 font-medium"> </th>
              <th className="text-muted-foreground py-3 pr-6 font-medium">
                Help-center chatbot
              </th>
              <th className="py-3 font-medium">Your agent</th>
            </tr>
          </thead>
          <tbody>
            {COMPARE.map((row) => (
              <tr key={row.row} className="border-b last:border-b-0">
                <th className="py-4 pr-6 font-medium">{row.row}</th>
                <td className="text-muted-foreground py-4 pr-6">{row.left}</td>
                <td className="py-4">{row.right}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Faq() {
  const [open, setOpen] = useState<number | null>(0)
  const baseId = useId()

  return (
    <section id="faq" className="page-section page-content">
      <SectionHeading eyebrow="FAQ" title="Straight answers." />
      <div className="max-w-3xl divide-y border-y">
        {FAQ_ITEMS.map((item, index) => {
          const panelId = `${baseId}-panel-${index}`
          const isOpen = open === index
          return (
            <div key={item.q}>
              <h3>
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-4 py-5 text-left text-[15px] font-medium"
                  aria-expanded={isOpen}
                  aria-controls={panelId}
                  onClick={() => setOpen(isOpen ? null : index)}
                >
                  {item.q}
                  <ChevronDown
                    className={`text-muted-foreground size-4 shrink-0 transition-transform duration-150 ${isOpen ? "rotate-180" : ""}`}
                  />
                </button>
              </h3>
              <div
                id={panelId}
                hidden={!isOpen}
                className="text-muted-foreground pb-5 text-[15px] leading-relaxed"
              >
                {item.a}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function ClosingCta() {
  return (
    <section className="page-section page-content">
      <h2 className="text-section max-w-xl">Ship the agent this week.</h2>
      <p className="text-muted-foreground mt-4 max-w-lg text-lg leading-relaxed">
        Create an account, upload a manual, register one action, paste the
        script tag.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Button size="lg" asChild>
          <Link
            to="/signup"
            onClick={() =>
              track({ event: "cta_get_started", placement: "footer_band" })
            }
          >
            Get started for free
          </Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link to="/login" onClick={() => track({ event: "cta_login" })}>
            Log in
          </Link>
        </Button>
      </div>
    </section>
  )
}
