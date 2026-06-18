#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 測試儀表板 — JARVIS-BRAIN Neural Vault v0.2
============================================================
獨立的測試環境，不影響原本日/月報流程。

設計目標：仿 Obsidian + 3D Graph View 的「作戰指揮室」風格
  · 多類別節點：persona / system / moc / project / note
  · Wikilink-style 連線
  · 左右多個浮動 panels：Dataview lists / MOC 樹 / AI chat / Stock ticker
  · Cyberpunk neon CSS + scanline 效果
  · 真實業務名作為 persona 節點（少量）+ 大量 hardcoded vault nodes
============================================================
"""
import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from itertools import combinations

sys.path.insert(0, '.')
from generate_daily import load_data, paid_orders, is_real_agent

META_VIDEOS_URL = 'https://vitokok-lab.github.io/meta-dashboard/data/videos.json'
TOP_VIDEOS = 25

OUTPUT_HTML = Path('./output/test.html')
TEMPLATE_HTML = Path('./data/templates/test_template.html')


# ═══════════════════════════════════════════════════════════
# 虛擬 Vault（hardcoded — 模擬 Obsidian 筆記網路）
# ═══════════════════════════════════════════════════════════

VAULT_NODES = [
    # === Persona (團隊角色 + AI) ===
    {'id': 'p:CMO_xiaowang',  'name': '小王',     'type': 'persona', 'sub': 'CMO · Mac mini',     'tier': 1},
    {'id': 'p:COO_yanxiong',  'name': '炎兄',     'type': 'persona', 'sub': 'COO · MacBook',      'tier': 1},
    {'id': 'p:UI_damaluo',    'name': '大瑪螺',   'type': 'persona', 'sub': 'UI/UX · Drone',      'tier': 2},
    {'id': 'p:AI_jarvis',     'name': 'JARVIS',   'type': 'persona', 'sub': 'AI Core',            'tier': 1},
    {'id': 'p:AI_claude',     'name': 'Claude',   'type': 'persona', 'sub': 'AI 群體組合 · LLM',  'tier': 2},
    {'id': 'p:AI_gpt',        'name': 'GPT-5',    'type': 'persona', 'sub': 'AI 群體組合',         'tier': 3},
    {'id': 'p:dev_aiko',      'name': '愛克',     'type': 'persona', 'sub': 'AI 助理 · 代理',     'tier': 2},

    # === System / Tool ===
    {'id': 's:POS',           'name': 'POS 機',   'type': 'system',  'sub': '門市結帳',           'tier': 1, 'status': '啟用中'},
    {'id': 's:1SHOP',         'name': '1SHOP',    'type': 'system',  'sub': '官網',               'tier': 1, 'status': '啟用中'},
    {'id': 's:LINE',          'name': 'LINE 社群','type': 'system',  'sub': 'OA + 群組',         'tier': 1, 'status': '啟用中'},
    {'id': 's:GBP',           'name': 'GBP 雙店', 'type': 'system',  'sub': 'Google 商家',         'tier': 2, 'status': '啟用中'},
    {'id': 's:Shopline',      'name': 'Shopline', 'type': 'system',  'sub': '訂單系統',           'tier': 1, 'status': '啟用中'},
    {'id': 's:Meta',          'name': 'Meta Ads', 'type': 'system',  'sub': 'FB + IG 廣告',       'tier': 2, 'status': '啟用中'},
    {'id': 's:GitHub',        'name': 'GitHub',   'type': 'system',  'sub': 'Code · Pages',       'tier': 2, 'status': '啟用中'},
    {'id': 's:Slack',         'name': 'Slack',    'type': 'system',  'sub': '溝通',               'tier': 3, 'status': '啟用中'},

    # === MOC (Map of Content) ===
    {'id': 'm:BRAIN',         'name': 'MOC_BRAIN',          'type': 'moc',     'sub': '主圖譜',     'tier': 1},
    {'id': 'm:THINK',         'name': 'MOC_思路鏈',         'type': 'moc',     'sub': 'Reasoning',  'tier': 2},
    {'id': 'm:FEED',          'name': 'feedback-na-app',    'type': 'moc',     'sub': '產品回饋',    'tier': 2},
    {'id': 'm:MASTER',        'name': '/master 整理東西處',  'type': 'moc',     'sub': 'A-Z',        'tier': 2},
    {'id': 'm:UX',            'name': '用戶體驗',           'type': 'moc',     'sub': 'UX Notes',    'tier': 3},
    {'id': 'm:BIZ',           'name': '視性回應',           'type': 'moc',     'sub': '訪談',       'tier': 3},

    # === Project (Kanban-like) ===
    {'id': 'pj:POS_intg',     'name': 'POS 整合',           'type': 'project', 'sub': '開發中',      'tier': 2},
    {'id': 'pj:1SHOP_v3',     'name': '1SHOP v3',           'type': 'project', 'sub': '籌備中',      'tier': 2},
    {'id': 'pj:LINE_auto',    'name': 'LINE 自動化',         'type': 'project', 'sub': '進行中',      'tier': 2},
    {'id': 'pj:GBP_local',    'name': 'GBP 本地化',          'type': 'project', 'sub': '籌備中',      'tier': 3},
    {'id': 'pj:Dashboard_v2', 'name': 'Dashboard v2',       'type': 'project', 'sub': '進行中',      'tier': 2},

    # === Note (零散筆記) ===
    {'id': 'n:彩寶指任',       'name': '彩寶指任',           'type': 'note',    'sub': '商品分類',    'tier': 3},
    {'id': 'n:寵粉策略',       'name': '寵粉策略',           'type': 'note',    'sub': '行銷',       'tier': 3},
    {'id': 'n:LINE_OA',       'name': 'LINE OA 分析',       'type': 'note',    'sub': '通路',       'tier': 3},
    {'id': 'n:會員等級',       'name': '會員等級設計',        'type': 'note',    'sub': 'CRM',        'tier': 3},
    {'id': 'n:庫存週轉',       'name': '庫存週轉',           'type': 'note',    'sub': '營運',       'tier': 3},
]

VAULT_LINKS = [
    # MOC 連到所有子物件
    ('m:BRAIN', 'm:THINK'), ('m:BRAIN', 'm:FEED'), ('m:BRAIN', 'm:MASTER'),
    ('m:BRAIN', 'm:UX'), ('m:BRAIN', 'm:BIZ'),
    ('m:BRAIN', 'p:AI_jarvis'),
    # Persona 互相連結
    ('p:CMO_xiaowang', 'p:COO_yanxiong'), ('p:COO_yanxiong', 'p:UI_damaluo'),
    ('p:CMO_xiaowang', 'p:AI_jarvis'), ('p:COO_yanxiong', 'p:AI_jarvis'),
    ('p:AI_jarvis', 'p:AI_claude'), ('p:AI_jarvis', 'p:AI_gpt'),
    ('p:AI_jarvis', 'p:dev_aiko'),
    # System ↔ Persona (誰在用什麼)
    ('p:CMO_xiaowang', 's:Meta'), ('p:CMO_xiaowang', 's:LINE'),
    ('p:COO_yanxiong', 's:Shopline'), ('p:COO_yanxiong', 's:GitHub'),
    ('p:UI_damaluo', 's:1SHOP'), ('p:UI_damaluo', 's:GBP'),
    ('p:dev_aiko', 's:Slack'), ('p:dev_aiko', 's:GitHub'),
    # System 之間
    ('s:Shopline', 's:POS'), ('s:Shopline', 's:1SHOP'), ('s:Shopline', 's:LINE'),
    ('s:Meta', 's:LINE'), ('s:Meta', 's:1SHOP'),
    ('s:Meta', 's:Shopline'),                            # 影音流量導購主管道
    # Project ↔ System
    ('pj:POS_intg', 's:POS'), ('pj:POS_intg', 's:Shopline'),
    ('pj:1SHOP_v3', 's:1SHOP'),
    ('pj:LINE_auto', 's:LINE'), ('pj:LINE_auto', 's:Meta'),
    ('pj:GBP_local', 's:GBP'),
    ('pj:Dashboard_v2', 's:GitHub'), ('pj:Dashboard_v2', 's:Shopline'),
    # Note ↔ MOC
    ('n:彩寶指任', 'm:MASTER'), ('n:寵粉策略', 'm:FEED'),
    ('n:LINE_OA', 'm:THINK'), ('n:會員等級', 'm:UX'),
    ('n:庫存週轉', 'm:BIZ'),
    # Note ↔ Persona/System
    ('n:LINE_OA', 's:LINE'), ('n:LINE_OA', 's:Meta'),
    ('n:寵粉策略', 'p:CMO_xiaowang'),
    ('n:會員等級', 's:Shopline'),
]


# ═══════════════════════════════════════════════════════════
# 真實業務（從 Shopline 抓 top 12 當「業務 persona」混進 graph）
# ═══════════════════════════════════════════════════════════

def build_real_agents():
    df = load_data()
    vd = paid_orders(df)
    cutoff = datetime.now() - timedelta(days=60)
    vd = vd[vd['訂單日期'] >= cutoff]
    if len(vd) == 0 or '推薦活動' not in vd.columns:
        return [], [], {}
    ccol = '顧客 ID' if '顧客 ID' in vd.columns else '顧客'
    vd_ag = vd[vd['推薦活動'].notna() & vd['推薦活動'].apply(is_real_agent)]
    if len(vd_ag) == 0:
        return [], [], {}
    ord_lvl = vd_ag.drop_duplicates('訂單號碼')
    agg = ord_lvl.groupby('推薦活動').agg(
        orders=('訂單號碼', 'count'),
        rev=('訂單合計', 'sum'),
        customers=(ccol, 'nunique'),
    ).reset_index().sort_values('rev', ascending=False).head(12)

    nodes = []
    for _, r in agg.iterrows():
        full = str(r['推薦活動'])
        name = full.split('/')[0].strip()
        if len(name) > 8:
            name = name[:8]
        nodes.append({
            'id': f'agent:{full}',
            'name': name,
            'type': 'agent',
            'sub': full,
            'tier': 2,
            'rev': int(r['rev']),
            'orders': int(r['orders']),
            'customers': int(r['customers']),
        })

    # 業務間共享客戶連線
    agent_ids = set(f'agent:{n["sub"]}' for n in nodes)
    cust_agents = (
        vd_ag.drop_duplicates(['訂單號碼'])
             .groupby(ccol)['推薦活動']
             .apply(lambda s: set(s.dropna()))
    )
    pair_count = {}
    for _, ag_set in cust_agents.items():
        if len(ag_set) > 1:
            for a, b in combinations(sorted(ag_set), 2):
                a_id, b_id = f'agent:{a}', f'agent:{b}'
                if a_id in agent_ids and b_id in agent_ids:
                    pair_count[(a_id, b_id)] = pair_count.get((a_id, b_id), 0) + 1
    links = [(a, b) for (a, b), v in pair_count.items() if v >= 2]

    total_ord = vd.drop_duplicates('訂單號碼')
    kpi = {
        'total_rev': int(total_ord['訂單合計'].sum()),
        'total_orders': int(len(total_ord)),
        'total_customers': int(vd[ccol].nunique()),
        'avg_aov': int(total_ord['訂單合計'].mean()) if len(total_ord) else 0,
        'period_label': '近 60 天',
    }
    return nodes, links, kpi


# ═══════════════════════════════════════════════════════════
# 影音資料（從 meta-dashboard）
# ═══════════════════════════════════════════════════════════

def fetch_video_data(top_n=TOP_VIDEOS):
    """抓 meta-dashboard 影音 JSON，回傳 top N 影片（按 plays 排序）"""
    try:
        req = urllib.request.Request(META_VIDEOS_URL, headers={'User-Agent': 'tzg-dashboard'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        videos = data.get('videos', {})
        sorted_videos = sorted(
            videos.values(),
            key=lambda v: -(v.get('plays', 0) or 0)
        )
        return sorted_videos[:top_n]
    except Exception as e:
        print(f'  [!] 影音資料抓取失敗（不阻擋）: {e}')
        return []


def build_video_nodes_links():
    """把 top N 影片轉成節點 + 連線（影片 → s:Meta → s:Shopline）"""
    videos = fetch_video_data(TOP_VIDEOS)
    nodes = []
    for v in videos:
        vid = str(v.get('id', ''))
        if not vid:
            continue
        title = (v.get('title') or '').replace('\n', ' ').strip()
        # 截斷顯示名稱
        if title:
            short = title[:8]
        else:
            short = f'video {vid[-5:]}'
        platform = (v.get('platform') or 'fb').upper()
        plays = int(v.get('plays', 0) or 0)
        reach = int(v.get('reach', 0) or 0)
        nodes.append({
            'id': f'v:{vid}',
            'name': short,
            'fullName': title or f'Video {vid}',
            'type': 'video',
            'sub': f'{platform} · {plays:,} 播放',
            'tier': 3,
            'platform': platform,
            'plays': plays,
            'reach': reach,
            'shares': int(v.get('shares', 0) or 0),
            'comments': int(v.get('comments', 0) or 0),
            'likes': int(v.get('likes', 0) or 0),
            'length_sec': int(v.get('length_sec', 0) or 0),
            'created_date': v.get('created_date', ''),
        })

    # 影片 → s:Meta（廣告渠道入口）
    # s:Meta → s:Shopline 連線在 VAULT_LINKS 加（如果還沒有）
    links = [(n['id'], 's:Meta') for n in nodes]
    return nodes, links


# ═══════════════════════════════════════════════════════════
# 構建 graph payload + UI sub-blocks
# ═══════════════════════════════════════════════════════════

def build_payload():
    agent_nodes, agent_links, kpi = build_real_agents()
    video_nodes, video_links = build_video_nodes_links()

    nodes = VAULT_NODES + agent_nodes + video_nodes
    links_raw = list(VAULT_LINKS) + agent_links + video_links

    # 業務 ↔ Shopline 連線
    for an in agent_nodes:
        links_raw.append((an['id'], 's:Shopline'))

    # 把連線轉成 graph 格式
    links = [{'source': a, 'target': b} for (a, b) in links_raw]

    # MOC 樹狀（給右上 panel 用）
    moc_tree = [
        {'name': 'MOC_BRAIN',           'children_count': 8, 'tag': 'core'},
        {'name': 'MOC_思路鏈',          'children_count': 5, 'tag': 'reason'},
        {'name': 'feedback-na-app...',  'children_count': 3, 'tag': 'fb'},
        {'name': '/master 整理東西處 A-Z', 'children_count': 26, 'tag': 'org'},
        {'name': '視性回應',             'children_count': 4, 'tag': 'biz'},
        {'name': '用戶體驗',             'children_count': 6, 'tag': 'ux'},
        {'name': '1Shop',               'children_count': 7, 'tag': 'sys'},
    ]

    # Dataview 風格清單
    top_videos_dv = []
    for vn in video_nodes[:5]:
        top_videos_dv.append({
            'name': vn['fullName'][:18] or vn['name'],
            'tag':  f'{vn["platform"]} · {vn["plays"]//1000}K',
            'mtime': vn.get('created_date', '') or '',
        })

    dataview_lists = {
        'ai_brain': [
            {'name': 'AI Core / JARVIS',     'tag': '#ai #core',   'mtime': '2026-06-18'},
            {'name': 'Claude 4.7 prompt 模板', 'tag': '#ai #prompt', 'mtime': '2026-06-17'},
            {'name': 'GPT-5 function call',  'tag': '#ai #tool',   'mtime': '2026-06-15'},
            {'name': 'Agent SDK pipeline',   'tag': '#ai #dev',    'mtime': '2026-06-12'},
            {'name': '對話歷史庫設計',         'tag': '#ai #memory', 'mtime': '2026-06-10'},
        ],
        'projects': [
            {'name': '彩寶指任',           'tag': '開發中',  'mtime': '2026-06-18'},
            {'name': 'POS 整合',          'tag': '開發中',  'mtime': '2026-06-17'},
            {'name': 'LINE 自動化',        'tag': '進行中',  'mtime': '2026-06-15'},
            {'name': '1SHOP v3',          'tag': '籌備中',  'mtime': '2026-06-10'},
            {'name': 'Dashboard v2',      'tag': '進行中',  'mtime': '2026-06-18'},
        ],
        'recent_notes': top_videos_dv or [  # 若抓不到影音則 fallback
            {'name': 'LINE OA 業績拆分',     'tag': '#analysis', 'mtime': '今天'},
            {'name': '寵粉策略檢討',          'tag': '#mkt',      'mtime': '今天'},
            {'name': '會員等級設計 v2',       'tag': '#crm',      'mtime': '昨天'},
            {'name': '客服 UTM 真實貢獻',     'tag': '#data',     'mtime': '6/16'},
            {'name': '月底推算業績算法',       'tag': '#dev',      'mtime': '6/16'},
        ],
    }

    # Stock ticker（假資料，後續可串 API）
    stock = {
        'symbol': '2330.TW',
        'name': '台積電',
        'price': 1075.0,
        'change': 12.0,
        'pct': 1.13,
    }

    # AI chat 假對話
    ai_chat = [
        {'who': 'JARVIS',  'msg': '本月 LINE OA 業績已達 NT$ 506K，扣寵粉後 NT$ 240K'},
        {'who': '小王',    'msg': '近 7 天日均下滑，建議減少 g 系列投放'},
        {'who': 'JARVIS',  'msg': '已分析 f24fb 廣告轉換率最高，建議追加預算 30%'},
    ]

    payload = {
        'nodes': nodes,
        'links': links,
        'kpi': kpi,
        'moc_tree': moc_tree,
        'dataview': dataview_lists,
        'stock': stock,
        'ai_chat': ai_chat,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    return payload


def main():
    print('=' * 60)
    print(' 🧠 TZG JARVIS-BRAIN Neural Vault v0.2')
    print('=' * 60)

    print('\n[1/3] 建立 Vault 結構...')
    data = build_payload()
    n_total = len(data['nodes'])
    n_agent = sum(1 for n in data['nodes'] if n['type'] == 'agent')
    n_video = sum(1 for n in data['nodes'] if n['type'] == 'video')
    n_vault = n_total - n_agent - n_video
    total_plays = sum(n.get('plays', 0) for n in data['nodes'] if n['type'] == 'video')
    print(f'  總節點:   {n_total} (vault {n_vault} + agent {n_agent} + video {n_video})')
    print(f'  總連線:   {len(data["links"])}')
    print(f'  MOC 樹:   {len(data["moc_tree"])} 個')
    print(f'  Dataview: {len(data["dataview"])} 個清單')
    if n_video:
        print(f'  📹 影音:   top {n_video} 支 / 累計播放 {total_plays:,}')

    print('\n[2/3] 套用模板...')
    if not TEMPLATE_HTML.exists():
        print(f'[✗] 找不到模板：{TEMPLATE_HTML}')
        sys.exit(1)
    html = TEMPLATE_HTML.read_text(encoding='utf-8')
    payload_json = json.dumps(data, ensure_ascii=False, default=str)
    html = html.replace('__GRAPH_DATA__', payload_json)

    print('\n[3/3] 寫檔...')
    OUTPUT_HTML.parent.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding='utf-8')
    size_kb = OUTPUT_HTML.stat().st_size // 1024
    print(f'[✓] 已生成：{OUTPUT_HTML}  ({size_kb} KB)')
    print()
    print('  本機預覽：  open output/test.html')
    print('  GitHub Pages:')
    print('    https://vitokok-lab.github.io/tzg-dashboard/output/test.html')


if __name__ == '__main__':
    main()
