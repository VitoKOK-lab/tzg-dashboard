# 泰熙爾札娜 · TAHIR ZAINAB — Design System

> 視覺與內容規範 · Visual & Content Guidelines
> A refined, white-dominant, feminine personal/lifestyle brand built for social-first publishing
> (Instagram feed, Stories & Highlights, profile). Traditional-Chinese primary language.

---

## 1. Brand context

**TAHIR ZAINAB (泰熙爾札娜)** is a boutique **jewelry / gemstone** brand with a cross-cultural
founding story — **Pakistan (星月, star & moon) meeting Taiwan (日, sun)** — expressed through a
celestial, talismanic visual world: compass roses, constellations (星宿), latitude/longitude
coordinates, gemstones (寶石) and sand (沙子). Its presence lives primarily on social media. The
identity is anchored by a single hand-drawn **calligraphic mark** — a fluid, brush-like glyph
flanked by two small diamond "sparkle" accents — paired with the uppercase Latin wordmark and the
Chinese name. A **signature floral pattern (品牌花紋)** is extracted from the mark and tiled across
packaging. The whole system is engineered for **clean, restrained, refined**
social posts: white-dominant canvases, peach-pink (桃紅) as the lead accent, gold (燙金) for
"soul" details, and a teal (泰熙爾藍) reserved almost entirely for ribbon/seal moments.

There is **no app or website** in scope. The "products" are the brand's social surfaces and its
publishing templates. UI kits in this system therefore recreate **publishing templates** (feed
posts, Story/Highlight covers, profile avatars) and an in-context social profile mock.

### Sources provided
- **Two logo files** (uploaded): a gold-on-pink mark (167×143 PNG) and a high-res black mark
  (3000×4000 PNG). Both recolored programmatically into the variants in `assets/`.
- **Written brand spec** (pasted): the five-color system with HEX/RGB/Pantone, the social color
  ratio, and account-visual rules (profile pic, Highlight covers, post colors).
- **No** codebase, Figma, slide deck, or typography spec was supplied. Type, neutrals, spacing,
  shadows, and components below are designed to fit the supplied palette and brief — see
  **Open assumptions** at the bottom.

---

## 2. The five-color system · 五色制

| Role | Name | HEX | RGB | Pantone |
|---|---|---|---|---|
| 主色 Primary | 札娜紅 · 桃紅 (Zana / peach-pink) | `#E6007E` | 230,0,126 | 213 C |
| 燙金 Gold | Gold 金 | `#C5B382` | 197,179,130 | 8640 C |
| 亮點 Highlight | 泰熙爾藍 (Tahir teal) | `#50C8BE` | 80,200,190 | 3258 C |
| 輔助 Secondary | 暗桃紅 (dark peach-pink) | `#B12468` | 177,36,104 | 215 C |
| 背景 Base | 純白 (pure white) | `#FFFFFF` | 255,255,255 | Bright White |

**Usage ratio (社群配色比例):** White is the dominant field. 桃紅 is the lead accent that guides
the eye. Gold appears only as a refined accent on precious/special elements. Teal (藍綠) is a
**soul accent** reserved for ribbon/seal-type details — never a large block. Avoid any large color
block outside the brand colors. Social posts read peach-pink-first with gold detailing.

All tokens (including derived tints, ink neutrals, and the metallic foil gradient) live in
[`colors_and_type.css`](colors_and_type.css).

---

## 3. Content fundamentals

**Language & voice.** Primary language is **Traditional Chinese (繁體中文)**, with the Latin
wordmark *TAHIR ZAINAB* used as a signature. Voice is **warm, refined, and quietly confident** —
like an elegant friend with impeccable taste. Never loud, never hard-sell.

**Casing.** The Latin wordmark is **「TAHIR ZAINAB」— uppercase, widely letter-spaced**, set in
Helvetica per the official logo artwork. English eyebrows/labels are also UPPERCASE with wide
tracking (`NEW ARRIVAL`, `LIMITED`).

**Person.** Speaks as an inclusive **「我們」/「你」** ("we" the brand, "you" the reader) — personal
and direct, e.g. 「追蹤我們」「為你準備」. Avoid corporate third-person.

**Punctuation & rhythm.** Use full-width Chinese punctuation（，。、）. Short, breathing lines.
A single thought per line on posts. Generous white space is part of the copy.

**Emoji.** **Avoid emoji.** The only decorative glyph permitted is the **diamond sparkle ✦ / ✧**
(echoing the logo's accents) and, sparingly, a star ★ for ratings. No 🌸💄✨ etc.

**Tone examples**
- Eyebrow → `NEW ARRIVAL · 新品`
- Hero → 「綻放的美，從一抹桃紅開始。」
- Body → 「以純白為底，桃紅作重點，金色點綴精緻細節。」
- CTA → 「立即選購」「尊享預約 ✦」「追蹤我們 →」
- Seal → 「✦ 泰熙爾認證 · Authentic」

**Do / Don't**
- ✅ Lead with one idea; let white space carry it. ✅ Uppercase tracked wordmark. ✅ Gold for the precious.
- ❌ Large non-brand color blocks. ❌ Emoji clutter. ❌ Shouty all-caps Chinese. ❌ Teal as a fill.

---

## 4. Visual foundations

**Overall vibe.** Editorial beauty-counter elegance: airy, white-dominant, with the peach-pink
doing the emotional work and gold supplying the "expensive" sparkle. Calm, feminine, premium.

**Color application.** White canvas → 桃紅 accent → gold detail → teal seal (see ratio above).
Backgrounds are overwhelmingly **pure white or barely-warm off-white** (`--paper-warm #FFFCFA`).
Soft pink tint panels (`--pink-050`) are allowed for gentle sectioning. Never a teal field.

**Type — official four-font system.**
- **中文主字體 (Chinese primary): 思源黑體 / 微軟正黑體** (Source Han Sans / Microsoft JhengHei) —
  titles, body, captions. The everyday workhorse.
- **英文主字體 (Latin primary): Helvetica** — English titles, the **brand name (TAHIR ZAINAB)**, and
  **all numbers** (prices, dates). Numbers are always upright Helvetica lining figures.
- **中文輔字體 (Chinese secondary): 思源宋體** (Source Han Serif) — brand story & contextual,
  emotive copy only.
- **英文輔字體 (Latin secondary): Georgia / serif** — English long-form & quotes / invoices.

思源黑體 = Noto Sans TC and 思源宋體 = Noto Serif TC (same fonts), so the system renders natively
in-browser via those families; Helvetica & Georgia are system/web-safe. Tokens: `--font-sans-tc`,
`--font-serif-tc`, `--font-sans` (Helvetica), `--font-serif` (Georgia) in `colors_and_type.css`.

**Spacing.** 8pt base scale, used generously. Air is a feature, not a gap to fill.

**Backgrounds.** No gradients as page fields (the only gradient is the **gold foil** used on small
details and the Story-ring). No heavy textures as social backgrounds. Imagery sits in clean
rectangles, often inside a hairline gold frame. Editorial, white-dominant compositions (think
Hermès on Instagram): lots of air, product photography as the hero, restrained pops of 桃紅.
Photography is **warm, bright, high-key** — peach/cream-leaning, soft natural light, minimal props.

**Corner radii.** Modest and refined — `sm 8 / md 14 / lg 22`, pill for buttons & chips. Avatars
and Story rings are full circles.

**Cards.** White fill, hairline border (`--line`/`--line-gold`), **soft low warm-tinted shadow**
(`--shadow-sm`). No hard borders, no colored left-accent bars, no neon.

**Shadows.** Soft, low, warm-tinted (plum-black at low alpha). `--shadow-pink` is a gentle glow
reserved for the primary pink CTA. No harsh black drop shadows.

**Borders.** Hairlines only — `1–1.5px`, in `--line` (pink-grey) or `--line-gold`. Gold hairline
rules are a signature divider.

**Pattern & ornament.** Two signature graphic systems sit on top of the foundations:
- **品牌花紋 (signature pattern):** a four-fold floral motif extracted from the logo mark, modularised
  and tiled. Used **tone-on-tone** on magenta (gift boxes, wrapping paper) and as gold-on-white on
  lighter goods. Assets: `assets/motif-{gold,pink,black,darkpink,softpink,white}.png` (transparent).
- **包裝紋樣 (celestial talisman):** an ornate astrolabe — compass coordinates (泰 30°N 70°E /
  台 22°N), sun & moon, constellations, gemstone glyphs and sunbursts framing the logo. Used as a
  hero medallion on premium **physical packaging** (gift boxes, wrapping paper) and print key
  visuals. Assets: `assets/celestial-astrolabe.png` (black/white) and `-gold.png` (transparent gold).
  **Print/packaging only — do NOT drop this artwork directly into social posts**; for digital, use
  clean editorial layouts (solid brand color or cream + type + logo + gold hairline).
Both are **fine gold linework**; never heavy fills. On busy pattern grounds, keep type inside a
clear white/solid medallion so it stays legible.

**Animation** *(for any motion work).* Slow, graceful, **ease-out / ease-in-out**, ~300–500ms.
Gentle fades and soft rises. **No bounce, no spring, no fast snaps.** Sparkle accents may twinkle
subtly. Restraint over energy.

**Hover / press** *(for interactive surfaces).* Hover = slight darken (pink → `--dark-pink`) or a
soft shadow lift; gold buttons brighten subtly. Press = small scale-down (~0.97) and shadow
reduction. Ghost buttons fill with `--pink-050` on hover. Never large color flips.

**Transparency & blur.** Used sparingly — a white scrim/protection gradient behind text over
imagery, occasional soft blur on overlays. Not a glassmorphism system.

**Layout rules.** Centered, symmetrical, generously margined compositions. Square (1080×1080) and
4:5 (1080×1350) for feed; 9:16 (1080×1920) for Stories; 1:1 circle-cropped for Highlight covers &
avatar. Keep the mark and key text within safe margins (≈8% inset).

---

## 5. Iconography

- **No built-in icon font shipped with the brand.** The brand's own iconographic vocabulary is the
  **diamond sparkle (✦ / ✧)** derived from the two accents flanking the logo mark, plus the
  occasional star (★) for ratings. These are used as Unicode glyphs in gold or pink.
- **Brand-story iconography:** the **celestial/talismanic glyph set** — sun, crescent moon & star,
  compass rose, constellation dots, gemstone facets, sunbursts, coordinate ticks — lives in the
  `celestial-astrolabe` artwork (`assets/`). Reuse by cropping from that artwork; do not redraw.
- **品牌花紋 (signature pattern):** the four-fold floral motif unit (`assets/motif-*.png`) is the
  brand's hero ornament — tile it, or use a single unit as a bullet / divider flourish.
- **UI / functional icons** (search, heart, share, chevrons, etc.) use **[Lucide](https://lucide.dev)**
  — a thin, even-stroke (1.75–2px) line set whose elegance matches the brand. Loaded from CDN in the
  UI kits. *This is a substitution* (no icon set was supplied) — flagged for review.
- **Highlight cover icons (限動 Highlight 封面):** rendered as **single Lucide line icons, centered
  on a white or pink circle, in one consistent brand color** — never multicolor, never filled. The
  set must read as one family (same stroke weight). Examples in `ui_kits/story-highlights/`.
- **Emoji:** not used (see Content Fundamentals).
- **Logo is not an icon** — never substitute the calligraphic mark for a UI glyph.

Real assets live in [`assets/`](assets/): the original uploads plus recolored mark variants
(`logo-{black,gold,pink,darkpink,teal,white}.png`, transparent background).

---

## 6. Index — what's in this folder

| Path | What it is |
|---|---|
| `README.md` | This document |
| `SKILL.md` | Agent-Skills entry point (for Claude Code etc.) |
| `colors_and_type.css` | All design tokens: colors, tints, foil, type, spacing, radii, shadows |
| `assets/` | Logo source files + recolored transparent mark variants |
| `preview/` | Design-System cards (colors, type, spacing, components, brand) |
| `ui_kits/post-templates/` | Feed-post templates (1:1 new-arrival, quote, 4:5 feature, announcement) |
| `ui_kits/story-highlights/` | 9:16 Story templates, Highlight cover set, avatar variations |
| `ui_kits/social-profile/` | Generic, brand-applied mobile social-profile mock (in context) |
| `screenshots/` | Working verification screenshots (not part of the deliverable) |

Each `ui_kits/<kit>/` has its own `README.md`, an interactive `index.html`, and small reusable
`.jsx` components. **No slide templates** were created (none were provided).

---

## 7. Open assumptions (please confirm / correct)

The intake questionnaire timed out, so the following were chosen to fit the palette and brief:

1. **Industry** read as refined **jewelry / gemstone (or beauty-lifestyle) personal brand** — the
   official dark-ground logo shot features red gemstones, which points to jewelry. Please confirm.
2. **Typefaces are now the official four-font system** (思源黑體/微軟正黑體, Helvetica, 思源宋體,
   Georgia) per your spec — implemented via Noto Sans/Serif TC + system Helvetica/Georgia. No
   custom font files are bundled; supply them if specific licensed cuts are required.
3. **Neutrals, tints, spacing, shadows, radii, components** are designed, not specified.
4. **Lucide** substituted for UI icons; **diamond ✦** treated as the native brand glyph.
5. The two uploaded marks are treated as the **same primary logo**; no secondary/monogram lockup
   was provided, so the wordmark lockup is typeset (best-match font).
