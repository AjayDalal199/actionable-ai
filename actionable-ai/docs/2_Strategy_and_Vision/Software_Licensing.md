# Software Licensing Guide: Actionable AI (A²I)

**Status:** Decision document. The repository is **currently MIT**. No license change has been made.

**This is not legal advice.** Licenses are copyright contracts. A lawyer licensed in your jurisdiction should review the final choice, the `LICENSE` file, customer Terms of Service, and any Contributor License Agreement before you ship, fundraise, or take the repo public under a new license.

---

## Why this document exists

The repo started from the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template), which is MIT-licensed. Our `LICENSE` file currently reads:

- Copyright (c) 2026 Actionable AI
- Copyright (c) 2019 Sebastián Ramírez (Full Stack FastAPI Template)

A²I is a **B2B SaaS product** (tiered paid backend; product strategy also calls for an **open-source embeddable widget**). The wrong license — or keeping MIT on the whole product by accident — can:

- Let a competitor fork the backend and sell it
- Force us to publish source if we later pull in a copyleft dependency
- Invalidate a future proprietary or “open core” model for code already released
- Create copyright problems with the FastAPI template if we drop its notice

This guide covers the licenses teams actually use, what they mean in practice, and a recommended path for this product.

---

## 1. Concepts (read this first)

| Term | Meaning |
| --- | --- |
| **Copyright** | The author owns the code by default. A license is permission they grant others. No license (and no public-domain dedication) means “all rights reserved.” |
| **License** | The terms under which others may use, copy, modify, and distribute the software. |
| **Trademark** | The name “Actionable AI” / logo. A software license almost never gives trademark rights. |
| **Patent grant** | Some licenses (Apache 2.0, GPLv3) explicitly license patents the contributor holds that the code practices. MIT does **not**. |
| **Permissive** | Few conditions. Downstream can keep the code closed. Typical: MIT, Apache 2.0, BSD. |
| **Copyleft (strong)** | If you distribute a derivative, you must share source under the same license. Typical: GPL, AGPL. |
| **Copyleft (weak / file-level)** | Only the copyleft files (or the library) stay open; the rest of the app can be proprietary. Typical: MPL, LGPL. |
| **Proprietary** | “All rights reserved.” Customers get a use license (SaaS ToS / EULA), not a right to copy the source. |
| **Source-available** | Source can be read, but OSI/open-source rules are not met (often “you may not offer this as a competing service”). Typical: BSL, SSPL, Elastic License. |
| **Distribution** | Copyleft usually triggers when you **convey** the software (ship a binary, give someone a repo). Running unmodified GPL on your own servers generally does **not** force you to publish source. **AGPL is the exception** (see below). |
| **Derivative work** | Modified copies, or (in many interpretations) a program that incorporates the licensed code. Linking and “mere aggregation” are argued over; treat GPL/AGPL dependencies as high risk until counsel agrees. |
| **SPDX id** | Short machine-readable license id (`MIT`, `Apache-2.0`, `GPL-3.0-only`). Put it in `LICENSE`, `package.json`, and `pyproject.toml`. |
| **Dual licensing** | Offer the same code under two licenses (e.g. AGPL **or** a paid proprietary license). Common for databases and developer tools. |
| **CLA / DCO** | Contributor License Agreement (you can relicense contributions) vs Developer Certificate of Origin (you assert you have the right to contribute). Needed if you accept outside PRs and may change license later. |

**Software license ≠ product Terms of Service.** Even a fully proprietary backend still needs customer ToS covering accounts, data processing, SLA, and acceptable use. The license governs the **code**. The ToS governs the **service**.

**Creative Commons is for writing, images, and data — not application source.** Do not put `CC-BY` or `CC-BY-SA` on Python/TypeScript. CC0 can dedicate docs or datasets to the public domain; still prefer an OSI license for code.

---

## 2. What the FastAPI template allows and forbids

MIT is **permissive**. We may:

- Keep the project MIT
- Use remaining template code inside a **proprietary** product
- Combine it with Apache 2.0, BSD, or (if we chose to) GPL
- Sell the software

We **must**, for as long as any substantial template code remains:

- Keep the MIT copyright and permission notice (Sebastián Ramírez, 2019, and our own copyright)
- Keep that notice in the `LICENSE` file and in copies we distribute

We **must not**:

- Delete the template copyright and pretend the leftover template files are solely ours
- Relicense **his** files as if they were originally GPL or proprietary-only (the MIT grant on those files stays with anyone who already received them)
- Assume “we rewrote everything” without a file-by-file check

**Already-published MIT code cannot be clawed back.** If this repo is or becomes public under MIT, anyone who obtained that revision keeps MIT rights to **that** code. We can apply a stricter license to **new** commits going forward. We cannot un-MIT yesterday’s tree.

Practical rule: **decide the product license before the repo is widely public**, or accept that early MIT snapshots stay MIT forever.

### If the repository stays private

**Keeping the git remote private is a valid, common setup for a paid SaaS.** Strangers cannot fork what they cannot see. The “MIT lets a competitor clone our backend” risk **does not apply** while access is limited to people you already trust (founders, employees, contractors under NDA / IP assignment).

Private does **not** mean “no copyright rules.” These still apply:

| Still required | Why |
| --- | --- |
| Keep the MIT notice for FastAPI template leftovers | MIT allows private use and commercial use, but the notice must remain in the software. Leaving `LICENSE` as-is is enough. |
| Honor dependency licenses | FastAPI, React, shadcn, etc. are fine (MIT/Apache/BSD). **AGPL** in the backend can still force source disclosure because customers **use the service over a network**, even if GitHub is private. GPL is mainly a problem if we **ship** images or binaries to customers. |
| Signed IP assignment (employees / contractors) | Private GitHub is not a substitute for “the company owns the code.” Without assignment, a contractor may still own what they wrote. |
| Customer Terms of Service / Privacy Policy | Users of the hosted product need a contract. That is separate from the repo license. |
| Treat the **widget JS** as distribution | Even with a private repo, script tags on customer sites **ship code** to browsers. That copy needs a license (proprietary ToS, or Apache if we open the widget). |

**What you can defer** if you are sure the repo will stay private and you will not open-source the widget soon:

- Switching the whole tree off MIT
- Apache 2.0 for the widget
- BSL / dual-license / CLA for outside contributors
- Publishing `THIRD_PARTY_NOTICES` (still do it before a commercial launch, but it is not urgent on day one)

**What still bites a private MIT repo:**

1. **Leak or mis-shared access.** Anyone who receives the tree under today’s `LICENSE` has MIT rights to that snapshot. A former contractor with a clone, a public gist, or “make this repo public for a minute” is enough.
2. **Later you go public.** Then MIT-on-everything becomes the problem described in §7. Change the license **before** that, or accept that old commits stay MIT.
3. **Copyleft dependencies.** Privacy of *our* source does not cancel AGPL/GPL obligations on *their* source.

**Working default if we stay private:** keep the current MIT `LICENSE` (required for the template), keep the repo private, use employment/contractor agreements, add product ToS when customers exist, and avoid AGPL/GPL dependencies. Revisit the open-core split only when we open the widget or the git remote.

---

## 3. Common licenses in detail

### 3.1 MIT License — `MIT`

**What it is.** Short permissive license. The default for this template and for much of the JavaScript ecosystem (including shadcn/ui).

**Permissions:** commercial use, modification, distribution, sublicensing, private use.

**Conditions:** keep the copyright notice and the MIT text.

**Limitations:** no warranty; **no explicit patent grant**.

**SaaS:** anyone can run it as a competing service. Anyone can close-source a fork.

**When people use it:** libraries, templates, SDKs, “we want adoption.”

**Fit for A²I:** fine for the **widget** and leftover **template files**. Risky as the **only** license on a paid backend you do not want cloned.

---

### 3.2 Apache License 2.0 — `Apache-2.0`

**What it is.** Permissive, longer than MIT. Used by Android, Kubernetes, and many company-backed SDKs.

**Permissions:** same commercial/modify/distribute as MIT, plus an **express patent license** from contributors.

**Conditions:** keep copyright, license, NOTICE file if present, and mark modified files. Patent license **terminates** if you sue the project for patent infringement.

**Limitations:** no trademark rights; no warranty.

**Compatibility:** you may include MIT/BSD code in an Apache project (keep their notices). You may **not** relicense Apache code as MIT. Apache 2.0 is compatible with GPLv3, **not** with GPLv2-only.

**SaaS:** still permissive — competitors can host it.

**When people use it:** company-owned open source, SDKs, anything where patents matter.

**Fit for A²I:** strongest default for an **open-source widget** (`packages/widget`). Better patent story than MIT if customers embed it in their product.

---

### 3.3 BSD licenses — `BSD-2-Clause`, `BSD-3-Clause`

**What they are.** Permissive, similar to MIT. 3-Clause adds “do not use our names to endorse derived products.”

**Permissions / conditions:** use, modify, distribute; keep copyright notice. 3-Clause no-endorsement.

**Limitations:** no warranty; no explicit patent grant (like MIT).

**When people use it:** older Unix/BSD world, some scientific and systems projects.

**Fit for A²I:** interchangeable with MIT for our purposes. No reason to switch the template to BSD.

---

### 3.4 ISC License — `ISC`

**What it is.** Functionally MIT with fewer words. Used by OpenBSD and historically by npm.

**Fit for A²I:** no advantage over MIT here.

---

### 3.5 GNU GPL v2 and v3 — `GPL-2.0-only`, `GPL-3.0-only`

**What they are.** Strong copyleft. Linux is GPLv2-only; many GNU programs are GPLv3.

**Permissions:** run, study, share, modify.

**Conditions:** if you **distribute** a binary or a derivative, you must provide complete corresponding source under the same GPL, plus installation information (v3, for locked devices). GPLv3 adds an explicit patent grant and blocks “tivoization.”

**Limitations:** you cannot take GPL code into a proprietary application and ship it without open-sourcing the derivative (how “linking” works is license- and counsel-specific).

**SaaS loophole:** hosting GPL software on **your** servers, without distributing it, generally does **not** require you to publish your modifications. That is why Affero GPL exists.

**Compatibility:** MIT/BSD/Apache-2.0 (into GPLv3) can flow **into** GPL. GPL cannot flow out into MIT or proprietary.

**Fit for A²I:** a poor fit for a commercial SaaS backend you want to keep closed. Using a **GPL Python dependency** inside a distributed backend image can contaminate the product. Audit dependencies.

---

### 3.6 GNU LGPL — `LGPL-2.1-only`, `LGPL-3.0-only`

**What it is.** “Lesser” GPL. Aimed at libraries.

**Idea:** you may link a proprietary application against an LGPL library if users can replace that library (dynamic linking and corresponding source of the LGPL part). Static linking and minified JS bundles need care.

**Fit for A²I:** relevant only if we **depend on** an LGPL library. Do not license our product as LGPL.

---

### 3.7 GNU Affero GPL v3 — `AGPL-3.0-only`

**What it is.** GPLv3 plus a **network-use** clause: if users interact with a modified version over a network, you must offer them the source.

**Why it exists:** to close the “SaaS loophole” in GPL.

**SaaS:** if our **backend** is AGPL, or we modify an AGPL component and expose it to customers, we likely must publish our corresponding source. MongoDB used AGPL, then left OSI licenses for SSPL for this class of reason.

**Fit for A²I:**

- **Do not** license the A²I backend as AGPL if the business model is closed SaaS.
- **Treat AGPL dependencies as a blocker** until counsel signs off. One AGPL library in the API process can force source disclosure.
- AGPL can be used **on purpose** as dual-license leverage (“AGPL or buy a commercial license”). That is a strategy, not an accident.

---

### 3.8 Mozilla Public License 2.0 — `MPL-2.0`

**What it is.** File-level weak copyleft (Firefox, and historically some HashiCorp code).

**Idea:** if you modify an MPL file, you must share those file-level changes under MPL. New files you write can stay proprietary. You may combine MPL and proprietary code in one program.

**Fit for A²I:** a possible middle ground if we wanted “improvements to our files come back” without GPL-ing the whole app. Unusual for a greenfield SaaS; more overhead than proprietary + Apache widget.

---

### 3.9 Unlicense / MIT-0 / CC0 — `Unlicense`, `MIT-0`, `CC0-1.0`

**What they are.** Public-domain dedication or “MIT with no attribution.”

**Fit for A²I:** do not use for the product. Attribution-free code is the opposite of protecting a commercial codebase. CC0 is reasonable for **sample datasets or purely informational docs**, not for the app.

---

### 3.10 Eclipse Public License 2.0 — `EPL-2.0`

**What it is.** Weak copyleft used in the Eclipse / Jakarta EE world. Similar spirit to MPL (copyleft on the EPL modules).

**Fit for A²I:** only relevant if we vendor EPL components.

---

### 3.11 European Union Public License — `EUPL-1.2`

**What it is.** Copyleft license from the European Commission, with a compatibility list (including GPL). Written with EU law in mind.

**Fit for A²I:** only if counsel specifically wants an EU-law-first copyleft. Not a typical SaaS product license.

---

### 3.12 Proprietary (“All rights reserved”)

**What it is.** No OSI license. Copyright retained. Others may use the software only as a contract allows (customer ToS, evaluation NDA, employee/contractor agreements).

**Permissions:** only what you grant (usually: use the hosted service; no right to copy, fork, or resell the source).

**Conditions:** defined in ToS / EULA / DPA.

**SaaS:** this is the normal model for the **paid control plane** (API, dashboard, RAG, billing).

**Template constraint:** proprietary A²I code can **include** remaining MIT template files if we **preserve MIT notices** for those portions.

**Fit for A²I:** recommended for `backend/` and the integrator dashboard, unless we explicitly choose open core for those too.

---

### 3.13 Source-available (not OSI “open source”)

These let people **read** source while blocking the use you actually care about (a rival hosted service). They are **not** Open Source as OSI defines it. GitHub will not label them as OSI licenses. Some customers and employees care about that distinction.

| License | SPDX / common name | Core extra restriction | Who used it |
| --- | --- | --- | --- |
| **Business Source License** | `BUSL-1.1` | Production use limited (often “no competing service”) until a change date, then it becomes an OSI license (often GPL or Apache). | MariaDB, Sentry (historically), CockroachDB (historically) |
| **SSPL** | Server Side Public License | If you offer the software as a service, you must open-source **the entire stack** used to provide that service. | MongoDB |
| **Elastic License** | Elastic License 2.0 | No providing the product as a managed service; no circumventing license keys. | Elasticsearch |
| **Commons Clause** | (add-on, not a full license) | “You may not Sell the software.” Bolted onto MIT/Apache; legally messy. | Some short-lived experiments |

**Fit for A²I:** optional **if** we want a public backend repo for trust/hiring but not a legal competitor cloud. Heavier than private proprietary source. Revisit only after a lawyer pass. BSL is the most common “we might open it later” choice.

---

### 3.14 Dual licensing

Offer **AGPL (or GPL) for community** and a **paid proprietary license** for customers who cannot consume copyleft (the MySQL / Qt model).

**Fit for A²I:** possible later for an on-prem backend. Unnecessary for MVP if the product is hosted-only. Requires a CLA so we own (or can relicense) every contribution.

---

## 4. Side-by-side comparison

| License | Can close-source a fork? | Must share source if we ship a derivative? | Must share source if we only host it? | Patent grant | Typical use |
| --- | --- | --- | --- | --- | --- |
| MIT / BSD / ISC | Yes | No | No | No | Libraries, templates |
| Apache 2.0 | Yes | No | No | Yes | Company SDKs, widgets |
| MPL 2.0 | Rest of app yes; changed MPL files no | Those files only | Generally no | Yes (limited) | File-level copyleft |
| LGPL | App yes, if linking rules met | Library changes | Generally no | v3 yes | Libraries |
| GPL v2/v3 | No | Yes, if distributed | **No** (hosted-only) | v3 yes | OS, tools you distribute |
| AGPL v3 | No | Yes, if distributed | **Yes** (network users) | Yes | Server software, dual-license |
| BSL / SSPL / Elastic | Restricted by extra terms | Depends | SSPL: effectively yes | Varies | Source-available SaaS cores |
| Proprietary | No (unless contract says so) | No | No | N/A (your patents) | Paid products |

“Can close-source” means a **downstream** recipient. It does not strip **our** copyright.

---

## 5. Third-party code: where trouble actually comes from

Our own `LICENSE` is only half the story. The app already depends on FastAPI, SQLModel, React, Vite, shadcn/ui, etc. Each dependency has its own license.

**Usually safe to combine with proprietary or Apache/MIT product code** (still keep notices): MIT, BSD, Apache 2.0, ISC, Unlicense.

**Needs a specific review:** LGPL, MPL, EPL (how we link or bundle), fonts and images (SIL OFL, CC), some data/model weights.

**High risk for a closed SaaS backend:**

- **GPL** if we distribute a Docker image or binaries that incorporate GPL code as a derivative
- **AGPL** if we run modified AGPL software as the service customers use
- **SSPL / Commons Clause** (rare in PyPI/npm, but do not copy-paste)

**Practical rules:**

1. Prefer MIT/Apache/BSD dependencies.
2. Do not add an AGPL or GPL library to `backend/` without an explicit decision recorded here.
3. Keep a `THIRD_PARTY_NOTICES` (or generate one in CI) before any commercial launch.
4. “AI-generated code” does not erase copyright in what it copied. Do not paste large chunks of GPL samples into the product.

Template-era UI (demo Items CRUD, etc.) stays MIT-licensed until removed or fully rewritten.

---

## 6. Models SaaS companies actually use

Aligned with [Product Strategy](./Product_Strategy.md): monetize the backend; open-source the widget.

| Model | Backend | Widget / SDK | What you get |
| --- | --- | --- | --- |
| **Accidental MIT-everything** (current default) | MIT | MIT | Maximum adoption; weakest moat; hard to undo after public clones |
| **Open core** (recommended direction) | Proprietary or BSL | Apache 2.0 | Competitors cannot legally ship our control plane; developers can fork the widget UI |
| **Fair source** | BSL / Elastic | Apache 2.0 | Public backend for trust; “no rival hosted product” clause |
| **AGPL dual license** | AGPL + paid closed license | Apache 2.0 | Pressure on-prem users to pay; hostile to some enterprises |
| **Fully closed** | Proprietary, private repo | Proprietary or Apache | Simplest legally; weaker developer-led growth for the embed |

---

## 7. Recommendation for Actionable AI

Until counsel says otherwise, treat this as the working policy:

### 7.1 Match the license to whether the source is public

If the git remote **stays private**, MIT on our new code is not an immediate competitive problem. Strangers cannot use a license they never received. See [If the repository stays private](#if-the-repository-stays-private).

If the source **is or will be public**, do not keep “the whole product is MIT” as the long-term plan. MIT on the **template leftovers** is required either way. MIT on **new backend, RAG, billing, and agent orchestration** then means anyone can legally host a competing A²I.

### 7.2 Split by component (open core)

| Tree | Recommended license | Why |
| --- | --- | --- |
| Remaining FastAPI template files | **MIT** (keep notices) | We do not have the right to strip that grant |
| `backend/` (API, workers, RAG, tools, billing) | **Proprietary** (All rights reserved) | This is the paid product |
| `frontend/` dashboard / marketing | **Proprietary** | Integrator console is product, not a community SDK |
| `packages/widget` (when it exists) | **Apache 2.0** | Matches “open-source the widget”; patent grant for embedders |
| `packages/` email templates | **Proprietary** or same as frontend | Operational, not a public SDK |
| Docs in `actionable-ai/docs/` | **Proprietary** or CC-BY-NC if we later want sharing without reuse as product copy | Optional; code license first |

A single repo can hold mixed licenses if `LICENSE` (or `LICENSE*` files) and headers say so clearly. Example pattern:

- `LICENSE` — short index: “See LICENSE.backend, LICENSE.widget, and notices for template MIT”
- `NOTICE` — template MIT text + third-party list
- SPDX headers on new files: `SPDX-License-Identifier: LicenseRef-Proprietary` vs `Apache-2.0`

### 7.3 Customer-facing legal (separate from this repo license)

- Terms of Service and Privacy Policy / DPA for the hosted API
- Widget Apache license **does not** grant customers rights to our API or their end-users’ data
- If the widget talks to our API, the ToS still applies to that use

### 7.4 Contributors

If the GitHub repo stays private and only employees/contractors commit, employment/contractor agreements that assign IP are enough **if they are signed**.

If we accept external PRs on an open widget:

- Use a **CLA** (or inbound = outbound Apache 2.0 with a DCO) so we can keep the widget Apache and the backend proprietary without relicensing fights.

### 7.5 What not to do

- Do not apply **AGPL** to the backend “to protect SaaS” without intending to publish source.
- Do not apply **Creative Commons** to TypeScript/Python.
- Do not delete Sebastián Ramírez’s MIT notice.
- Do not announce Apache/proprietary in README while `LICENSE` still says MIT-only — the files must match.
- Do not copy GPL snippets, AGPL server examples, or random GitHub files into the agent/tooling code.

---

## 8. How to apply a chosen license (when we decide)

1. **Lawyer review** of the split (proprietary backend + Apache widget + MIT template remainder).
2. **Inventory** files still substantially from the FastAPI template; list them in `NOTICE`.
3. Replace the single MIT-as-product-license story:
   - Keep MIT text for template portions
   - Add proprietary terms for A²I original work
   - Add `LICENSE.widget` (Apache 2.0) when `packages/widget` ships
4. Set SPDX / `license` fields in `backend/pyproject.toml` and future `packages/widget/package.json`.
5. Add a short **copyright header** to new source files.
6. Add **dependency license CI** (e.g. allowlist MIT/Apache/BSD; fail on GPL/AGPL).
7. Update [README](../../../README.md) License section so it describes the split, not “MIT” alone.
8. If the repo is public, **tag the last MIT-everywhere revision** so history stays honest.

Until those steps happen, the legal reality is: **the project is MIT**, including new A²I code we have been adding on top of the template.

---

## 9. Decision log

| Date | Decision | Owner |
| --- | --- | --- |
| 2026-08-25 | Document written. Current SPDX: `MIT`. Recommended future: proprietary platform + Apache 2.0 widget + retained template MIT. **Not yet adopted.** | Engineering / founding team |
| 2026-08-25 | If the repo stays private, MIT-everywhere is acceptable for now; the open-core split is for when source or the widget goes public. | Engineering / founding team |

**Open questions for counsel and founders:**

1. Confirm the git remote stays private (and who has clone access).
2. Confirm employment/contractor IP assignment exists.
3. Approve proprietary vs BSL only if the backend will be public later.
4. Confirm Apache 2.0 (not MIT) for the widget **when** we open-source it.
5. Jurisdiction for copyright notices (company legal name, not only “Actionable AI”).

---

## 10. Official texts (use these, do not paraphrase into `LICENSE`)

| License | Canonical text |
| --- | --- |
| MIT | https://opensource.org/license/mit |
| Apache 2.0 | https://www.apache.org/licenses/LICENSE-2.0 |
| BSD-3-Clause | https://opensource.org/license/bsd-3-clause |
| GPL-3.0 | https://www.gnu.org/licenses/gpl-3.0.html |
| AGPL-3.0 | https://www.gnu.org/licenses/agpl-3.0.html |
| LGPL-3.0 | https://www.gnu.org/licenses/lgpl-3.0.html |
| MPL-2.0 | https://www.mozilla.org/en-US/MPL/2.0/ |
| BSL 1.1 | https://mariadb.com/bsl-faq-adopting/ |
| SPDX list | https://spdx.org/licenses/ |

Choose one of the official texts. Do not invent a hybrid “MIT but you cannot compete with us” — that is a different license (and may fail as both MIT and as enforceable custom terms).

---

## Related product docs

- [Product Strategy](./Product_Strategy.md) — open-source widget, monetize backend
- [PRD](../3_Product_Definition_and_Scoping/PRD.md)
- Root [`LICENSE`](../../../LICENSE) — current MIT grant (template + A²I)
- Root [`README.md`](../../../README.md) — currently states MIT
