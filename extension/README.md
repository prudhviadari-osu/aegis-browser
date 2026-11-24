# extension/ — the fill-and-review browser extension (not built yet)

This half of `aegis-browser` is the **only** component that touches a live
application form — and it does so safely:

- Runs in **your real, logged-in browser** (Chrome/Edge, Manifest V3) — not headless,
  not a separate session.
- On a job application page, it fills fields from your profile (jobify provides the
  draft), **highlights what it filled, and STOPS.**
- **You review and click submit.** It never submits for you.

It will be built after the headless wrapper is in real use (see ../DESIGN.md §6, §8).
Placeholder for now so the repo structure matches the design.
