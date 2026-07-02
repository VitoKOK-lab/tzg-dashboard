---
name: tahir-zainab-design
description: Use this skill to generate well-branded interfaces and assets for TAHIR ZAINAB (泰熙爾札娜) — a celestial-themed fine-jewelry / gemstone brand — for production or throwaway prototypes/mocks. Contains essential design guidelines, the five-color system, the four-font type system, fonts, logo & motif assets, and social UI-kit components for prototyping (feed posts, stories, highlight covers, profile).
user-invocable: true
---

# TAHIR ZAINAB · 泰熙爾札娜 — Design Skill

Read `README.md` first for the full system (brand context, five-color palette, four-font type
system, content fundamentals, visual foundations, iconography). Then explore:

- `colors_and_type.css` — all design tokens (colors, tints, gold foil, type, spacing, radii,
  shadows). Import or copy this into any artifact.
- `assets/` — logo mark in many colors (`logo-{black,gold,pink,darkpink,teal,white}.png`),
  optically-centered avatar crops (`logo-square-*.png`), the signature pattern unit
  (`motif-*.png`), and the celestial packaging artwork (`celestial-astrolabe*.png`).
- `ui_kits/` — `post-templates/`, `story-highlights/`, `social-profile/`. Each has a README, an
  interactive `index.html`, and reusable `.jsx` components.

## Working rules
- **Palette:** white-dominant. 桃紅 `#E6007E` leads; gold `#C5B382` is for refined detail; teal
  `#50C8BE` only for ribbon/seal accents. Avoid large non-brand color blocks.
- **Type:** 思源黑體/微軟正黑體 (Chinese primary), Helvetica (Latin titles, **brand name**, numbers),
  思源宋體 (Chinese story/emotive), Georgia (Latin long-form). Wordmark = `TAHIR ZAINAB`, uppercase,
  wide-tracked. No emoji; the only decorative glyph is the diamond ✦.
- **Look:** editorial, airy, luxury restraint (Hermès-on-IG). Hairline gold rules, soft shadows,
  modest radii, generous white space.
- **Packaging artwork** (`celestial-astrolabe`) is for print/physical packaging — keep it out of
  social posts; use clean editorial layouts for digital.

## When invoked
If creating visual artifacts (slides, mocks, throwaway prototypes), copy assets out and produce
static HTML files for the user to view. If working on production code, copy assets and apply the
rules here to design as an expert in this brand.

If invoked with no other guidance, ask what the user wants to build or design, ask a few focused
questions, then act as an expert designer who outputs HTML artifacts **or** production code as
needed.
