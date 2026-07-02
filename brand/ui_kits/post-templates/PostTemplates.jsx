/* TAHIR ZAINAB — Post templates (editorial / luxury restraint). Authored at real 1080px. */
const ASSET = '../../assets';

function Frame({ w = 1080, h = 1080, display = 350, children, style = {}, onClick, selected }) {
  const scale = display / w;
  return (
    <div onClick={onClick} style={{
      width: display, height: h * scale, borderRadius: 8, overflow: 'hidden',
      boxShadow: selected ? '0 0 0 3px var(--zana-pink),0 18px 40px rgba(43,24,34,.16)' : 'var(--shadow-md)',
      cursor: onClick ? 'pointer' : 'default', flex: 'none', transition: '.2s ease', background: '#fff',
    }}>
      <div style={{ width: w, height: h, transformOrigin: 'top left', transform: `scale(${scale})`, position: 'relative', ...style }}>{children}</div>
    </div>
  );
}

const Eyebrow = ({ children, color = 'var(--gold-deep)', center }) => (
  <div style={{ fontFamily: 'var(--font-sans)', fontSize: 22, letterSpacing: '.4em', textTransform: 'uppercase', color, textAlign: center ? 'center' : 'left', paddingLeft: center ? '.4em' : 0 }}>{children}</div>
);
const Hair = ({ w = 90, center }) => (
  <div style={{ width: w, height: 1, background: 'var(--gold-deep)', margin: center ? '0 auto' : 0, opacity: .8 }} />
);
const Wordmark = ({ color = 'var(--ink)', center }) => (
  <div style={{ fontFamily: 'var(--font-sans)', fontSize: 22, letterSpacing: '.42em', color, textAlign: center ? 'center' : 'left', paddingLeft: center ? '.42em' : 0 }}>TAHIR ZAINAB</div>
);

/* 1 — editorial product (1:1, white, airy) */
function NewArrivalPost(props) {
  return (
    <Frame {...props}>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '96px 110px', boxSizing: 'border-box' }}>
        <img src={`${ASSET}/logo-gold.png`} style={{ height: 58 }} />
        <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '40px 0 36px' }}>
          <image-slot id="ta-newarrival" shape="rect" style={{ width: 560, height: 560, border: '1px solid var(--gold-300)' }} placeholder="拖入商品照"></image-slot>
        </div>
        <Eyebrow center>New In</Eyebrow>
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 58, color: 'var(--ink)', marginTop: 22, letterSpacing: '.04em' }}>星月流光耳環</div>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 30, color: 'var(--ink-soft)', marginTop: 16, letterSpacing: '.04em' }}>NT$ 4,880</div>
      </div>
    </Frame>
  );
}

/* 2 — quote (1:1, cream, restrained) */
function QuotePost(props) {
  return (
    <Frame {...props} style={{ background: 'var(--paper-warm)' }}>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '120px 130px', boxSizing: 'border-box' }}>
        <div style={{ color: 'var(--gold-deep)', fontSize: 40, marginBottom: 44 }}>✦</div>
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 62, lineHeight: 1.7, color: 'var(--ink)' }}>每一顆寶石，<br />都是一次跨越座標的相遇。</div>
        <div style={{ margin: '52px 0 40px' }}><Hair w={70} center /></div>
        <Wordmark center color="var(--ink-soft)" />
      </div>
    </Frame>
  );
}

/* 3 — feature (4:5, editorial framed photo + caption) */
function FeaturePost(props) {
  return (
    <Frame w={1080} h={1350} {...props}>
      <div style={{ position: 'absolute', inset: 0, background: '#fff', display: 'flex', flexDirection: 'column', padding: '84px 90px', boxSizing: 'border-box' }}>
        <image-slot id="ta-feature" shape="rect" style={{ width: '100%', height: 720, border: '1px solid var(--gold-300)' }} placeholder="拖入情境照"></image-slot>
        <div style={{ marginTop: 54 }}>
          <Eyebrow>Limited Edition</Eyebrow>
          <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 56, color: 'var(--ink)', marginTop: 18, letterSpacing: '.03em' }}>暗夜星砂手鍊</div>
          <div style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 26, color: 'var(--ink-soft)', marginTop: 12 }}>巴基斯坦星砂 · 18K 燙金扣</div>
          <div style={{ height: 1, background: 'var(--line)', margin: '30px 0 26px' }} />
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 40, color: 'var(--ink)' }}>NT$ 6,280</span>
            <span style={{ fontFamily: 'var(--font-sans-tc)', fontSize: 28, color: 'var(--dark-pink)', letterSpacing: '.08em' }}>了解更多 →</span>
          </div>
        </div>
      </div>
    </Frame>
  );
}

/* 4 — announcement (1:1, solid deep magenta, editorial — no print artwork) */
function CelestialPost(props) {
  return (
    <Frame {...props} style={{ background: '#B12468' }}>
      <div style={{ position: 'absolute', inset: 56, border: '1px solid rgba(255,255,255,.35)', borderRadius: 4 }} />
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 140, boxSizing: 'border-box' }}>
        <img src={`${ASSET}/logo-white.png`} style={{ height: 84, marginBottom: 50, opacity: .95 }} />
        <Eyebrow center color="var(--gold-300)">Coming Soon</Eyebrow>
        <div style={{ fontFamily: 'var(--font-serif-tc)', fontWeight: 500, fontSize: 74, color: '#fff', lineHeight: 1.4, marginTop: 26 }}>星月系列<br />全新登場</div>
        <div style={{ margin: '40px 0 30px' }}><Hair w={64} center /></div>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 28, color: 'var(--gold-300)', letterSpacing: '.3em' }}>06 · 18</div>
      </div>
    </Frame>
  );
}

const POST_CAPTIONS = {
  NewArrival: '✦ 星月流光耳環・新品上市\n以巴基斯坦的星與月為靈感，燙金弧線勾勒夜空。\n\n#TAHIRZAINAB #泰熙爾札娜 #新品 #耳環',
  Quote: '每一顆寶石，都是一次跨越座標的相遇。\n從 30°N 70°E，到台灣的日光。\n\n#TAHIRZAINAB #品牌故事 #寶石',
  Feature: '暗夜星砂手鍊・限量\n巴基斯坦星砂 × 18K 燙金扣，附泰熙爾藍緞帶封條。\n\n#TAHIRZAINAB #限量 #手鍊',
  Celestial: '✦ COMING SOON\n星月系列・06.18 全新登場。\n羅盤指向你我相遇的座標。\n\n#TAHIRZAINAB #星月系列 #新品預告',
};

Object.assign(window, { Frame, Eyebrow, Hair, Wordmark, NewArrivalPost, QuotePost, FeaturePost, CelestialPost, POST_CAPTIONS });
