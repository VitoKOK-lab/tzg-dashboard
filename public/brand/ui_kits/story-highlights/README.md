# UI Kit — Stories & Highlights · 限動・精選・大頭貼

Vertical Story templates (9:16), unified Highlight covers, and circular profile avatars.

## Files
- `index.html` — interactive showcase (click a Story to select; drag a photo onto the slot).
- `StoryHighlights.jsx` — Story templates, `HighlightCover`, `HIGHLIGHTS` set.
- `image-slot.js` — user-fillable photo placeholder.

## Contents
| Component | Notes |
|---|---|
| `ProductStory` (1080×1920) | Full-bleed photo + ink protection gradient + “向上滑・選購” pill |
| `QuoteStory` | Magenta tone-on-tone pattern, white logo, 思源宋體 line |
| `TeaserStory` | Gold celestial astrolabe on ink — launch teaser |
| `HighlightCover` | Lucide line icon on a brand circle — `variant="pink"` (主) / `"white"` (替代) |

## Highlight covers (限動封面)
Per brand spec: **統一品牌色圖示、風格一致**. One icon family (Lucide, even stroke), one circle
treatment. Primary = white icon on 桃紅 circle; alternate = 桃紅 icon on white circle. Set:
新品(sparkles)・寶石(gem)・故事(moon-star)・座標(compass)・禮盒(gift)・評價(heart).

> **Icon substitution:** Lucide (CDN) stands in for a bespoke icon set — same even-stroke, refined
> line style. Flagged in the root README's Iconography section.

## Avatars (大頭貼)
Circular crop of the mark. Three grounds: white (with Story ring), 桃紅, ink + 燙金. Uses the
optically-centered `assets/logo-square-*.png`.
