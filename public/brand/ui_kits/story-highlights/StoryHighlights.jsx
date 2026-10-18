/* TAHIR ZAINAB — Story & Highlight components (authored at real px, scaled) */
const SH_ASSET = '../../assets';

function StoryFrame({ display = 248, children, style = {}, selected, onClick }) {
  const w = 1080, h = 1920, scale = display / w;
  return (
    <div onClick={onClick} style={{
      width: display, height: h * scale, borderRadius: 16, overflow: 'hidden', flex: 'none',
      boxShadow: selected ? '0 0 0 3px var(--zana-pink),0 18px 40px rgba(43,24,34,.16)' : 'var(--shadow-md)',
      cursor: onClick ? 'pointer' : 'default', transition: '.2s ease', background: '#fff',
    }}>
      <div style={{ width: w, height: h, transformOrigin: 'top left', transform: `scale(${scale})`, position: 'relative', ...style }}>
        {children}
      </div>
    </div>
  );
}

/* status bar + tap dots for realism */
const StoryChrome = ({ n = 3, active = 0, dark }) => (
  <div style={{ position: 'absolute', top: 30, left: 30, right: 30, display: 'flex', gap: 8, zIndex: 5 }}>
    {Array.from({ length: n }).map((_, i) => (
      <div key={i} style={{ flex: 1, height: 5, borderRadius: 3, background: dark ? 'rgba(255,255,255,.4)' : 'rgba(43,24,34,.18)' }}>
        <div style={{ width: i <= active ? '100%' : 0, height: '100%', borderRadius: 3, background: dark ? '#fff' : 'var(--zana-pink)' }} />
      </div>
    ))}
  </div>
);

/* 1 — product story (image + shop) */
function ProductStory(props) {
  return (
    <StoryFrame {...props}>
      <StoryChrome active={0} dark />
      <image-slot id="ta-story-prod" shape="rect" style={{ position: 'absolute', inset: 0, width: 1080, height: 1920 }} placeholder="拖入直式商品照"></image-slot>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 760, background: 'linear-gradient(to top, rgba(43,24,34,.78), transparent)' }} />
      <div style={{ position: 'absolute', left: 70, right: 70, bottom: 150, color: '#fff' }}>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 30, letterSpacing: '.3em', textTransform: 'uppercase', color: 'var(--gold-300)', marginBottom: 18 }}>New In</div>
        <div style={{ fontFamily: 'var(--font-sans-tc)', fontWeight: 700, fontSize: 86, lineHeight: 1.15 }}>星月流光耳環</div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 16, marginTop: 40, background: '#fff', color: 'var(--ink)', fontFamily: 'var(--font-sans-tc)', fontSize: 40, padding: '26px 50px', borderRadius: 999 }}>向上滑・選購 ↑</div>
      </div>
    </StoryFrame>
  );
}

/* 2 — quote story (solid deep magenta, editorial — no print artwork) */
function QuoteStory(props) {
  return (
    <StoryFrame {...props} style={{ background: '#B12468' }}>
      <StoryChrome active={1} dark />
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 110, boxSizing: 'border-box' }}>
        <img src={`${SH_ASSET}/logo-white.png`} style={{ height: 110, marginBottom: 60, opacity: .95 }} />
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 74, lineHeight: 1.65, color: '#fff' }}>從 30°N 70°E，<br />到你的耳畔。</div>
        <div style={{ marginTop: 60, width: 120, height: 1.5, background: 'var(--gold-300)' }} />
      </div>
    </StoryFrame>
  );
}

/* 3 — launch teaser (cream editorial — no print artwork) */
function TeaserStory(props) {
  return (
    <StoryFrame {...props} style={{ background: 'var(--paper-warm)' }}>
      <StoryChrome active={2} />
      <div style={{ position: 'absolute', inset: 60, border: '1px solid var(--gold-300)', borderRadius: 6 }} />
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 130, boxSizing: 'border-box' }}>
        <img src={`${SH_ASSET}/logo-gold.png`} style={{ height: 90, marginBottom: 56 }} />
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 28, letterSpacing: '.4em', textTransform: 'uppercase', color: 'var(--gold-deep)', paddingLeft: '.4em' }}>Coming Soon</div>
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 88, color: 'var(--ink)', marginTop: 28 }}>星月系列</div>
        <div style={{ margin: '46px 0 34px', width: 80, height: 1, background: 'var(--gold-deep)' }} />
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 34, color: 'var(--ink-soft)', letterSpacing: '.3em' }}>06 · 18</div>
      </div>
    </StoryFrame>
  );
}

/* Highlight cover — Lucide line icon on a consistent brand circle */
function HighlightCover({ icon, label, variant = 'pink' }) {
  const pink = variant === 'pink';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: 78, height: 78, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: pink ? 'var(--zana-pink)' : '#fff', border: pink ? 'none' : '1px solid var(--line)',
        boxShadow: 'var(--shadow-xs)',
      }}>
        <i data-lucide={icon} style={{ width: 30, height: 30, color: pink ? '#fff' : 'var(--zana-pink)' }}></i>
      </div>
      <span style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 12.5, color: 'var(--ink-soft)' }}>{label}</span>
    </div>
  );
}

const HIGHLIGHTS = [
  { icon: 'sparkles', label: '新品' }, { icon: 'gem', label: '寶石' }, { icon: 'moon-star', label: '故事' },
  { icon: 'compass', label: '座標' }, { icon: 'gift', label: '禮盒' }, { icon: 'heart', label: '評價' },
];

Object.assign(window, { StoryFrame, StoryChrome, ProductStory, QuoteStory, TeaserStory, HighlightCover, HIGHLIGHTS });
