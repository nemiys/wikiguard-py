---
name: wikiguard-notion
description: Update wikiguard-py's Notion project page at the end of a completed Stage — the 4-section format (על הפרויקט incl. stage roadmap + per-stage summaries / טכנולוגיות + איך מיושמות / תובנות עקרוניות / צמתי החלטה), not the old מבט-על/העמקה טכנית skill format used by other bootcamp projects. Invoke at the end of each Stage, once.
---

# wikiguard-py Notion update

Updates the single Notion page that documents this project, per the doc
strategy in this repo's `CLAUDE.md` ("תיעוד — חובה, בסוף כל Stage") and
`docs/architecture-plan.md`. Runs **once per completed Stage**, not more
often — this mirrors the ADR-vs-Notion split: ADRs are written immediately
per decision, this page is updated once the Stage is done.

## Page identity

- URL: https://app.notion.com/p/3dd3d71444a58198a7bffd168d43d525
- Title: "wikiguard-py — Real-Time Wikipedia Edit Monitor"
- Location: database "🗂️ מאגר ידע — Resources" (path: 🌱 אישי / 🗺️ התפתחות
  אישית / 🗂️ מאגר ידע — Resources), data source
  `collection://d55a7c52-8bba-4972-8b6c-9f1e195076ed`
- This page uses the **new**, deliberately simpler 3-section format — do
  **not** create מבט-על/העמקה טכנית sub-pages like the other bootcamp
  projects in the same database use (that's the old, more verbose format
  this project explicitly moved away from).

## The four sections (fixed, don't add more)

1. **על הפרויקט** — the descriptive text is written once, only touched again
   if the project's scope changes materially. It also contains:
   - A **stage roadmap table** (Stage 0-8, what's built, status) — updated
     every stage (flip the just-completed stage's status), unlike the
     surrounding prose.
   - Right after that table, **one short paragraph per completed stage**
     (2-4 sentences: what was built and why, at the level of the intro given
     in chat before each stage starts — not the full blow-by-blow). Add one
     new paragraph per stage, in order.
   Both additions were made 2026-09-17 after the user asked for the full
   roadmap and a short per-stage summary to be visible on the page, not just
   the "current stage" sentence.
2. **טכנולוגיות + איך מיושמות** — a cumulative table. Add a new row only for
   a technology/library that actually became meaningfully used in the stage
   just completed (not everything planned for the future). Columns:
   טכנולוגיה | תפקיד | הערה. The last line of the "על הפרויקט" section has an
   "עדכון זה: אחרי Stage N (...)" sentence — update it to the stage just
   closed each time (this sentence lives in "על הפרויקט", not this table).
3. **תובנות עקרוניות** — added 2026-09-17. Not a transcript of every
   question asked in chat — only genuinely principled/important issues that
   came up (a conceptual correction, a non-obvious mechanism, a "why does it
   have to work this way" resolution). Judgment call each time; most stages
   may add nothing here. Keep each item to 2-4 sentences, same tight style
   as an ADR summary line, not a full re-derivation of the chat discussion.
4. **צמתי החלטה** — one line per *significant* decision (same bar as ADRs:
   hard/expensive to change later, or shapes how other parts get built),
   each a 1-2 sentence "what and why" in simple Hebrew + a pointer to the
   matching `docs/adr/NNNN-slug.md` file. Do not duplicate the ADR's full
   reasoning here. Only add a line when a **new** ADR was written in the
   stage just completed — most stages won't need a change here. (Includes
   ADR-0006, written retroactively for a Stage 1 decision once its
   significance became clear in Stage 3 discussion — it's fine for an ADR to
   lag its stage when this happens, as long as it's written before being
   referenced here.)

## How to update it (mechanical steps)

1. **Always `notion-fetch` the page first**, even if you think you remember
   its content — you need the *exact* stored text to do a search-and-replace
   with `notion-update-page`'s `update_content` command.
2. **The table is stored as HTML-ish tags, not Markdown pipes** — Notion
   round-trips it as `<table header-row="true"><tr><td>...</td>...</tr>...
   </table>`, even though you originally wrote it as Markdown pipe syntax.
   Match `old_str` against the `<tr>...</tr>` block exactly as fetched, not
   against how you'd naturally write a new row.
3. To add rows: use `content_updates` with `old_str` = the last existing
   `<tr>...</tr>...</table>` (closing tag included) and `new_str` = that same
   last row + your new `<tr>` row(s) + `</table>`. This appends without
   needing `replace_all_matches`.
4. Update the "עדכון זה: אחרי Stage N" sentence in a separate `content_updates`
   entry in the same call (old_str = the current sentence, new_str = the
   updated one naming the stage and a short parenthetical of what it added).
5. Only touch "צמתי החלטה" if a **new** ADR file was actually created this
   stage — append one line the same way, matching against the existing last
   bullet + the closing italic note about the repo not being on GitHub yet.
6. Don't touch "על הפרויקט" unless the user confirms the project's scope
   actually changed.

## Known caveat (until the repo has a GitHub remote)

The "צמתי החלטה" section's ADR links currently point to local file paths
(`docs/adr/NNNN-slug.md`), with a note that they'll become real GitHub URLs
once the repo is pushed. When that happens, that's a one-time bulk link
update — check whether it's been done before repeating the local-path
pattern in a new line.
