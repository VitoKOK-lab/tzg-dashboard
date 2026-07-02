# UI Kit — Post Templates · 貼文模板

Social feed-post templates for TAHIR ZAINAB, applying the brand system (white-dominant, 桃紅 lead,
gold motif, celestial medallion). Authored at real export sizes and scaled for display.

## Files
- `index.html` — interactive showcase. Click a template to preview its suggested caption; **拖入**
  (drag) your own product photo onto the dashed image slots.
- `PostTemplates.jsx` — the template components + `POST_CAPTIONS` sample copy.
- `image-slot.js` — user-fillable photo placeholder (starter component).

## Templates
| Component | Size | Use |
|---|---|---|
| `NewArrivalPost` | 1080×1080 | New-product launch — circular product shot, gold motif corners |
| `QuotePost` | 1080×1080 | Brand-story quote on magenta tone-on-tone pattern, white medallion |
| `FeaturePost` | 1080×1350 (4:5) | Product feature — hero photo + price + CTA |
| `CelestialPost` | 1080×1080 | Announcement / teaser over the gold celestial astrolabe |

## Rules applied
- White or magenta grounds only; **桃紅 leads, gold details, no large non-brand blocks.**
- Brand name & all numbers (prices, dates) in **Helvetica**; Chinese in **思源黑體**; story copy in
  **思源宋體**. Eyebrows UPPERCASE, wide-tracked.
- The signature motif (`assets/motif-*.png`) and celestial artwork (`assets/celestial-*`) are reused,
  never redrawn.
- Captions: lead with one idea, ✦ sparkle allowed, no emoji, hashtags `#TAHIRZAINAB #泰熙爾札娜`.

> Note: image slots persist only when the host file is at project root; in this sub-folder they act
> as clean placeholders for the showcase.
