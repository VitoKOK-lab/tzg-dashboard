# UI Kit — Social Profile · 社群主頁

A generic (non-platform-specific) mobile social profile with the TAHIR ZAINAB brand applied
end-to-end — to show the system in real context. Not a clone of any platform's proprietary UI.

## Files
- `index.html` — interactive profile inside a phone frame (tap 追蹤 to toggle follow state; the
  feed uses real image slots for product photography).
- `Profile.jsx` — `StatusBar`, `TopBar`, `Header`, `Actions`, `HighlightTray`, `Tabs`, `FeedGrid`.
- `image-slot.js` — user-fillable photo placeholder.

## What it demonstrates
- **Avatar** with Story ring (optically-centered mark).
- **Bio block** — name in 思源黑體, `FINE JEWELRY · 寶石訂製` eyebrow in Helvetica, story line in
  思源宋體, link in 桃紅.
- **Follow / message** actions — primary 桃紅 vs hairline secondary.
- **Highlight tray** — white icons on 桃紅 circles (Lucide).
- **Feed grid** — editorial & white-dominant (Hermès-style restraint): mostly product photography
  (image slots) interleaved with light brand tiles — one magenta logo tile, cream motif, soft-pink
  motif, a typographic wordmark tile, and a 思源宋體 quote. **No large non-brand blocks; no print
  packaging artwork** (the celestial astrolabe is reserved for physical packaging only).

## Icons
Lucide (CDN) — even-stroke line set, substitution flagged in the root README.
