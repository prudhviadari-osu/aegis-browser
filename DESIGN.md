# aegis-browser — Design Doc

A **general, domain-agnostic Playwright wrapper** for headless browser work. It
knows how to drive a browser (navigate, read, extract, screenshot) — and knows
nothing about jobs, study, or any domain. Aegis and its skills (jobify, later
learn++) borrow it when they need the web beyond what clean APIs provide.

Status: design (pre-build). New repo: `aegis-browser`.

---

## 1. Why this exists (the role in the system)

The three-repo system:

```
AEGIS  = brain + environment. Orchestrates skills; can use aegis-browser directly
         (research, reading docs, general browsing).
   │
   ├── uses ──▶ aegis-browser   = general headless browser wrapper (Playwright).
   │                               Domain-agnostic. No login, no form-fill.
   │
   └── runs ──▶ SKILLS (separate, by domain):
                 • jobify   — job domain. Owns job search + application PREP.
                              Calls aegis-browser to read a found job's
                              requirements page and gather drafting material.
                 • learn++  — study domain (later). Same pattern.
```

**The key boundaries this design enforces:**
- **aegis-browser is general** — it does browser ops, not job/study logic.
- **Domain logic lives in the skill** — jobify owns everything job-specific
  (including the apply/prep logic); learn++ will own study logic. Aegis stays generic.
- **Aegis is the brain** — it decides *when* to use the browser and *which* skill
  runs; it doesn't contain domain logic either.

This is the cleaner separation the user asked for: Aegis = environment/brain,
skills = domain experts, aegis-browser = a shared capability both can call.

---

## 2. What headless is FOR (and firmly NOT for)

### Headless IS for: reading public pages
- Fetching a **found job's application-requirements page** (what fields/questions/
  documents it needs) — the thing APIs don't expose.
- General **research / reading** for Aegis (an article, a docs page, a company's
  about page).
- Extracting text/structured content, taking a screenshot for a record.

All of this is **public-page reading**. No account, no credentials, no forms.

### Headless is NOT for (hard safety line):
- **No logging into your accounts.** It never touches your Workday/Gmail/etc. login.
- **No filling or submitting applications.** That is exclusively the job of the
  **fill-and-review browser extension** (separate piece, §6), which runs in *your*
  real, logged-in browser session under your supervision.
- **No mass automated actions against sites that forbid it.**

Why the line matters: headless automation logged into your real account is
detectable and risks your account + your professional reputation. Reading public
pages is low-risk and legitimate. The extension keeps the risky part (filling your
real application) as supervised, human-driven, in-your-own-session work.

---

## 3. Repo layout

```
aegis-browser/
├── DESIGN.md                 (this doc)
├── README.md                 (how it's used, esp. with Aegis)
├── pyproject.toml
├── browser/                  # the Playwright wrapper (headless, public reading)
│   ├── __init__.py
│   ├── client.py             # BrowserClient: the general API surface (§4)
│   ├── extract.py            # text / links / structured extraction helpers
│   └── safety.py             # URL allow/deny checks; enforces 'no login pages'
├── extension/                # the fill-and-review browser extension (Manifest V3)
│   │                         #   (built later; lives here so the 'browser' repo
│   │                         #    holds both halves — headless read + assisted fill)
│   └── README.md             # placeholder until built
└── tests/                    # offline tests (mock Playwright; no real browser)
```

Two halves, one repo — matching "overall repo for browser applications":
- `browser/` = headless **reading** (safe, general, Playwright).
- `extension/` = assisted **filling** in your real session (the only thing that
  touches a live form; built after the headless half works).

---

## 4. The wrapper API (general, domain-agnostic)

`BrowserClient` — a thin, safe wrapper over Playwright. The whole point is it
exposes *general* browser ops, so Aegis can use it for research and jobify can use
it for requirements-reading, with no job/study concepts baked in.

```python
class BrowserClient:
    def __init__(self, headless: bool = True, timeout: int = 20): ...

    def fetch(self, url: str) -> PageResult:
        """Navigate to a PUBLIC url, return extracted content. Refuses login/auth
        pages (safety.py). The workhorse for reading a page."""

    def extract_text(self, url: str) -> str:
        """Just the readable text of a page."""

    def extract_structured(self, url: str, selectors: dict) -> dict:
        """Pull named fields by CSS selector, e.g.
        {'title': 'h1', 'requirements': '.job-requirements'}."""

    def screenshot(self, url: str, path: str) -> str:
        """Save a screenshot (a record / for your review)."""

    def close(self) -> None: ...


@dataclass
class PageResult:
    url: str
    final_url: str          # after redirects
    title: str
    text: str               # readable text
    links: list[str]
    ok: bool
    error: str = ""
```

Design notes:
- **One browser context per client**, reused across calls; `close()` tears down.
- **Timeouts on everything** (never hang the caller).
- **safety.py gate**: `fetch()` refuses URLs that look like login/auth/account
  pages (`/login`, `/signin`, `accounts.`, SSO hosts…) — a hard stop so headless
  can't wander into an authenticated flow.
- **Polite**: a real User-Agent, a small delay option, respects obvious blocks;
  no hammering.

---

## 5. How the skills use it

### jobify (job domain) — application PREP
jobify keeps its existing API-based *fetching* (Workday/Greenhouse/Lever JSON — faster,
safer than a browser). The new part, which lives **in jobify**:

```
job found (via APIs)  →  jobify.apply_prep.gather_requirements(job)
                              └─ uses aegis-browser.fetch(job.url) to read the
                                 public application page: required fields, questions,
                                 documents, deadlines.
                         →  jobify drafts the application from the profile + the
                            gathered requirements (its existing analyzer/draft logic).
                         →  result stored; shown in Aegis's /jobs review page.
```

So: **jobify owns the job-apply logic; it borrows the browser from aegis-browser.**
Aegis never learns about Workday forms.

### Aegis (brain) — general research
Aegis can call `aegis-browser` directly for non-job tasks, e.g. a future "research"
skill: `fetch(url)` an article, summarize it with the local model. Domain-agnostic
use of the same wrapper.

---

## 6. The fill-and-review extension (later half)

Built after the headless half works. Manifest V3 extension that:
- Runs in **your real, logged-in browser** (not headless, not a separate session).
- On a job application page, fills fields from your profile (jobify provides the
  draft), **highlights what it filled, and STOPS.**
- **You review and click submit.** It never submits for you.

This is the only component that touches a live application form, and it does so as
supervised, in-your-session, human-driven work — the safe way to actually apply.

---

## 7. Testing reality (honest)

- The headless wrapper is tested **offline with a mocked Playwright** (the sandbox,
  and CI, have no real browser). Logic (safety gate, extraction, error handling) is
  unit-tested; real-page behavior must be verified by **you** running it on your Mac.
- The **extension cannot be tested here at all** — you load it in Chrome and test on
  real pages, reporting back. Building it is partly "blind," relying on you as eyes.

---

## 8. Build order
1. **`BrowserClient` + safety gate + extraction** (headless reading), offline-tested.
2. **jobify `apply_prep`** — gather requirements for a found job via the wrapper +
   draft from profile. (Lives in jobify.)
3. **Aegis research use** — a thin path for Aegis to use the wrapper for general reading.
4. **The extension** (fill + review) — last, and tested by you in Chrome.

---

## 9. Non-goals
- Not a general web-automation framework (that's just Playwright — we wrap it thinly).
- No headless login, no headless form submission, no mass auto-apply.
- No domain logic in aegis-browser (jobs/study logic belongs in the skills).
