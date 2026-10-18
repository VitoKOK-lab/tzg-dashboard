/* TAHIR ZAINAB — Generic social profile (brand-applied, not a platform clone) */
const P_ASSET = '../../assets';

const Icon = ({ n, size = 22, color = 'var(--ink)', sw = 2 }) => (
  <i data-lucide={n} style={{ width: size, height: size, color, strokeWidth: sw }}></i>
);

function StatusBar() {
  return (
    <div style={{ height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', fontFamily: 'var(--font-sans)', fontSize: 15, fontWeight: 600, color: 'var(--ink)' }}>
      <span>9:41</span>
      <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}><Icon n="signal" size={16} sw={2.4} /><Icon n="wifi" size={16} sw={2.4} /><Icon n="battery-full" size={20} sw={2} /></span>
    </div>
  );
}

function TopBar() {
  return (
    <div style={{ height: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 18px', borderBottom: '1px solid var(--line)' }}>
      <Icon n="chevron-left" size={26} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontFamily: 'var(--font-sans-tc)', fontWeight: 700, fontSize: 17 }}>
        <img src={`${P_ASSET}/logo-pink.png`} style={{ height: 18 }} />tahirzainab
      </div>
      <Icon n="menu" size={24} />
    </div>
  );
}

function Header() {
  return (
    <div style={{ padding: '18px 18px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
        <div style={{ width: 86, height: 86, borderRadius: '50%', padding: 3, background: 'linear-gradient(135deg,var(--zana-pink),var(--gold))', flex: 'none' }}>
          <div style={{ width: '100%', height: '100%', borderRadius: '50%', border: '3px solid #fff', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            <img src={`${P_ASSET}/logo-square-pink.png`} style={{ width: '80%', height: '80%', objectFit: 'contain' }} />
          </div>
        </div>
        <div style={{ display: 'flex', flex: 1, justifyContent: 'space-around', textAlign: 'center' }}>
          {[['248', '貼文'], ['37.4k', '粉絲'], ['126', '追蹤']].map(([n, l]) => (
            <div key={l}><div style={{ fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 19, color: 'var(--ink)' }}>{n}</div><div style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 12.5, color: 'var(--ink-soft)' }}>{l}</div></div>
          ))}
        </div>
      </div>
      <div style={{ marginTop: 14 }}>
        <div style={{ fontFamily: 'var(--font-sans-tc)', fontWeight: 700, fontSize: 15 }}>TAHIR ZAINAB 泰熙爾札娜</div>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--gold-deep)', marginTop: 3 }}>Fine Jewelry · 寶石訂製</div>
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontSize: 13.5, color: 'var(--ink-soft)', lineHeight: 1.6, marginTop: 6 }}>星月 × 日，跨越座標的相遇 ✦<br />巴基斯坦寶石・台灣手作・全球配送</div>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--zana-pink)', marginTop: 5 }}>tahirzainab.com/shop</div>
      </div>
    </div>
  );
}

function Actions({ following, onToggle }) {
  return (
    <div style={{ display: 'flex', gap: 8, padding: '14px 18px 4px' }}>
      <button onClick={onToggle} style={{ flex: 1, fontFamily: 'var(--font-sans-tc)', fontWeight: 500, fontSize: 14, letterSpacing: '.06em', padding: '9px', borderRadius: 3, border: following ? '1px solid var(--line)' : 'none', background: following ? '#fff' : 'var(--zana-pink)', color: following ? 'var(--ink)' : '#fff', cursor: 'pointer' }}>{following ? '追蹤中 ✓' : '追蹤'}</button>
      <button style={{ flex: 1, fontFamily: 'var(--font-sans-tc)', fontWeight: 500, fontSize: 14, padding: '9px', borderRadius: 3, border: '1px solid var(--line)', background: '#fff', color: 'var(--ink)' }}>訊息</button>
      <button style={{ width: 40, borderRadius: 3, border: '1px solid var(--line)', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Icon n="bookmark" size={18} /></button>
    </div>
  );
}

const HL = [['sparkles', '新品'], ['gem', '寶石'], ['moon-star', '故事'], ['compass', '座標'], ['gift', '禮盒']];
function HighlightTray() {
  return (
    <div style={{ display: 'flex', gap: 18, padding: '16px 18px', overflowX: 'auto' }}>
      {HL.map(([icon, label]) => (
        <div key={icon} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 'none' }}>
          <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--zana-pink)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 0 1px #fff, 0 0 0 2px var(--gold-300)' }}><Icon n={icon} size={23} color="#fff" sw={1.6} /></div>
          <span style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 11.5, color: 'var(--ink-soft)' }}>{label}</span>
        </div>
      ))}
    </div>
  );
}

function Tabs() {
  return (
    <div style={{ display: 'flex', borderTop: '1px solid var(--line)' }}>
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '11px 0', borderBottom: '1.5px solid var(--ink)' }}><Icon n="grid-3x3" size={22} /></div>
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '11px 0' }}><Icon n="bookmark" size={22} color="var(--ink-faint)" /></div>
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '11px 0' }}><Icon n="user-square" size={22} color="var(--ink-faint)" /></div>
    </div>
  );
}

/* feed tiles — art-directed tonal editorial grid (champagne / blush restraint) */
const PRODUCT_TONES = [
  { bg: 'linear-gradient(150deg,#FBF6EA 0%,#F3ECDB 100%)', label: '燙金細節' },
  { bg: 'linear-gradient(150deg,#FCEFF6 0%,#F7DEEC 100%)', label: '星月耳環' },
  { bg: 'linear-gradient(150deg,#FAF4F0 0%,#F0E6E0 100%)', label: '星砂手鍊' },
  { bg: 'linear-gradient(150deg,#FBF7F0 0%,#EFE8DC 100%)', label: '寶石戒指' },
];
function ProductTile({ idx }) {
  const t = PRODUCT_TONES[idx % PRODUCT_TONES.length];
  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '1/1', overflow: 'hidden', background: t.bg }}>
      <div style={{ position: 'absolute', inset: 11, border: '1px solid rgba(151,124,68,.28)' }} />
      <img src={`${P_ASSET}/motif-gold.png`} style={{ position: 'absolute', top: '50%', left: '50%', width: '46%', transform: 'translate(-50%,-58%)', opacity: .42 }} />
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 22, textAlign: 'center', fontFamily: 'var(--font-serif-tc)', fontSize: 12.5, letterSpacing: '.14em', color: 'var(--gold-deep)' }}>{t.label}</div>
    </div>
  );
}

function Tile({ kind, idx }) {
  const base = { position: 'relative', width: '100%', aspectRatio: '1/1', overflow: 'hidden' };
  if (kind === 'magenta')
    return <div style={{ ...base, background: 'radial-gradient(120% 120% at 30% 20%, #C01C75 0%, #A11F60 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14 }}><img src={`${P_ASSET}/logo-white.png`} style={{ width: '36%' }} /><div style={{ fontFamily: 'var(--font-sans)', fontSize: 9.5, letterSpacing: '.36em', paddingLeft: '.36em', color: 'rgba(255,255,255,.82)' }}>TAHIR ZAINAB</div></div>;
  if (kind === 'cream-motif')
    return <div style={{ ...base, background: 'var(--paper-warm)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><img src={`${P_ASSET}/motif-gold.png`} style={{ width: '50%', opacity: .9 }} /></div>;
  if (kind === 'wordmark')
    return <div style={{ ...base, background: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, border: '1px solid var(--line)', boxSizing: 'border-box' }}><div style={{ color: 'var(--gold-deep)', fontSize: 15 }}>✦</div><div style={{ fontFamily: 'var(--font-sans)', fontSize: 12.5, letterSpacing: '.32em', paddingLeft: '.32em', color: 'var(--ink)' }}>TAHIR ZAINAB</div><div style={{ width: 28, height: 1, background: 'var(--gold-deep)', opacity: .7 }} /><div style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 10.5, letterSpacing: '.36em', paddingLeft: '.36em', color: 'var(--ink-soft)' }}>泰熙爾札娜</div></div>;
  if (kind === 'quote')
    return <div style={{ ...base, background: 'var(--paper-warm)', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 16, boxSizing: 'border-box' }}><span style={{ fontFamily: 'var(--font-serif-tc)', fontSize: 15, lineHeight: 1.8, color: 'var(--ink)' }}>跨越座標的<br />相遇</span></div>;
  return <ProductTile idx={idx} />;
}

const FEED = ['magenta', 'product', 'cream-motif', 'product', 'wordmark', 'product', 'product', 'quote', 'product'];
function FeedGrid() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 3, background: 'var(--line)', padding: 0 }}>
      {FEED.map((k, i) => <Tile key={i} kind={k} idx={i} />)}
    </div>
  );
}

Object.assign(window, { Icon, StatusBar, TopBar, Header, Actions, HighlightTray, Tabs, FeedGrid });
