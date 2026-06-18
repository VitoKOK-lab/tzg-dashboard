#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 測試儀表板 — JARVIS-BRAIN Neural Vault v1.0
============================================================
獨立的測試環境，不影響原本日/月報流程。

純真實資料：
  · 影片節點：meta-dashboard/data/videos.json（top by plays）
  · 業務節點：Shopline 訂單推薦活動（近 60 天）
  · 錨點系統：Meta（影音流量入口）、Shopline（成交系統）

資料流：影片 → Meta → Shopline ← 業務

產出：output/test.html
============================================================
"""
import json
import sys
import re
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from itertools import combinations

sys.path.insert(0, '.')
from generate_daily import load_data, paid_orders, is_real_agent

OUTPUT_HTML = Path('./output/test.html')
TEMPLATE_HTML = Path('./data/templates/test_template.html')
META_VIDEOS_URL = 'https://vitokok-lab.github.io/meta-dashboard/data/videos.json'
TOP_VIDEOS = 30
TOP_AGENTS = 15
LOOKBACK_DAYS = 60


# ═══════════════════════════════════════════════════════════
# 錨點：兩個真實對應的系統節點（影片要連、業務要連）
# ═══════════════════════════════════════════════════════════
ANCHOR_NODES = [
    {'id': 's:Meta',     'name': 'Meta',     'type': 'anchor', 'sub': 'FB + IG 影音流量入口', 'tier': 1},
    {'id': 's:Shopline', 'name': 'Shopline', 'type': 'anchor', 'sub': '訂單成交系統',         'tier': 1},
]
ANCHOR_LINKS = [
    ('s:Meta', 's:Shopline'),   # 流量導購主管道
]


# ═══════════════════════════════════════════════════════════
# 真實業務節點 (近 60 天 Shopline 訂單)
# ═══════════════════════════════════════════════════════════
def build_real_agents():
    df = load_data()
    vd = paid_orders(df)
    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
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
    ).reset_index().sort_values('rev', ascending=False).head(TOP_AGENTS)

    nodes = []
    for _, r in agg.iterrows():
        full = str(r['推薦活動'])
        name = full.split('/')[0].strip()
        if len(name) > 8:
            name = name[:8]
        nodes.append({
            'id': f'agent:{full}',
            'name': name,
            'fullName': full,
            'type': 'agent',
            'sub': full[:22],
            'tier': 2,
            'rev': int(r['rev']),
            'orders': int(r['orders']),
            'customers': int(r['customers']),
            'aov': int(r['rev'] / r['orders']) if r['orders'] else 0,
        })

    # 業務間共享客戶連線
    agent_ids = set(f'agent:{n["fullName"]}' for n in nodes)
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
        'period_label': f'近 {LOOKBACK_DAYS} 天',
    }
    return nodes, links, kpi


# ═══════════════════════════════════════════════════════════
# 真實影音節點 (meta-dashboard)
# ═══════════════════════════════════════════════════════════
def fetch_video_data(top_n=TOP_VIDEOS):
    try:
        req = urllib.request.Request(META_VIDEOS_URL, headers={'User-Agent': 'tzg-dashboard'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        videos = data.get('videos', {})
        sorted_videos = sorted(
            videos.values(),
            key=lambda v: -(v.get('plays', 0) or 0)
        )
        return sorted_videos[:top_n], data.get('updated_at', ''), data.get('count', 0)
    except Exception as e:
        print(f'  [!] 影音資料抓取失敗（不阻擋）: {e}')
        return [], '', 0


def build_video_nodes_links():
    videos, updated_at, total_count = fetch_video_data(TOP_VIDEOS)
    nodes = []
    for v in videos:
        vid = str(v.get('id', ''))
        if not vid:
            continue
        title = (v.get('title') or '').replace('\n', ' ').strip()
        short = title[:8] if title else f'video {vid[-5:]}'
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
    # 影片全連 s:Meta
    links = [(n['id'], 's:Meta') for n in nodes]
    return nodes, links, updated_at, total_count


# ═══════════════════════════════════════════════════════════
# 真實 UTM 渠道分布 (近 60 天 top 5)
# ═══════════════════════════════════════════════════════════
def build_utm_channels():
    df = load_data()
    vd = paid_orders(df)
    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    vd = vd[vd['訂單日期'] >= cutoff]
    if 'UTM 來源/媒介' not in vd.columns:
        return []
    vd_uniq = vd.drop_duplicates('訂單號碼')

    def classify(s):
        s = str(s).strip().lower()
        if not s or s == 'nan':
            return '直接 / 官網'
        if s.startswith('line/'): return 'LINE OA'
        if s.startswith('fb/') or 'facebook' in s: return 'Facebook'
        if s.startswith('ig/') or 'instagram' in s: return 'Instagram'
        if s.startswith('shopline'): return 'SHOPLINE Email'
        return '其他'

    vd_uniq = vd_uniq.copy()
    vd_uniq['_src'] = vd_uniq['UTM 來源/媒介'].fillna('').apply(classify)
    g = vd_uniq.groupby('_src').agg(
        orders=('訂單號碼', 'count'),
        rev=('訂單合計', 'sum'),
    ).reset_index().sort_values('rev', ascending=False).head(5)
    total_rev = vd_uniq['訂單合計'].sum()
    out = []
    for _, r in g.iterrows():
        pct = r['rev'] / total_rev * 100 if total_rev else 0
        out.append({
            'name': r['_src'],
            'tag': f'NT$ {int(r["rev"]/1000):,}K',
            'mtime': f'{pct:.1f}%',
        })
    return out


# ═══════════════════════════════════════════════════════════
# 組裝 payload
# ═══════════════════════════════════════════════════════════
def build_payload():
    agent_nodes, agent_links, kpi = build_real_agents()
    video_nodes, video_links, updated_at, total_videos = build_video_nodes_links()
    utm_channels = build_utm_channels()

    nodes = list(ANCHOR_NODES) + agent_nodes + video_nodes
    links_raw = list(ANCHOR_LINKS) + agent_links + video_links

    # 業務 → Shopline（每位都連，視覺化所有真實業務與成交系統的連線）
    for an in agent_nodes:
        links_raw.append((an['id'], 's:Shopline'))

    links = [{'source': a, 'target': b} for (a, b) in links_raw]

    # 3 個真實 Dataview 清單
    top_videos_dv = []
    for vn in video_nodes[:6]:
        top_videos_dv.append({
            'name': vn['fullName'][:18] or vn['name'],
            'tag':  f'{vn["platform"]} · {vn["plays"]//1000}K',
            'mtime': vn.get('created_date', '') or '',
        })
    top_agents_dv = []
    for an in agent_nodes[:6]:
        top_agents_dv.append({
            'name': an['fullName'][:18],
            'tag':  f'NT$ {an["rev"]//1000:,}K',
            'mtime': f'{an["orders"]} 單',
        })

    # 額外計算 KPI：影音播放總數
    total_plays = sum(v['plays'] for v in video_nodes)
    kpi['total_plays'] = total_plays
    kpi['video_count'] = total_videos
    kpi['video_updated_at'] = updated_at

    payload = {
        'nodes': nodes,
        'links': links,
        'kpi': kpi,
        'dataview': {
            'top_videos': top_videos_dv,
            'top_agents': top_agents_dv,
            'utm_channels': utm_channels,
        },
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    return payload


def main():
    print('=' * 60)
    print(' 🧠 TZG JARVIS-BRAIN Neural Vault v1.0 (純真實資料)')
    print('=' * 60)

    print('\n[1/3] 抓取真實資料...')
    data = build_payload()
    n_total = len(data['nodes'])
    n_video = sum(1 for n in data['nodes'] if n['type'] == 'video')
    n_agent = sum(1 for n in data['nodes'] if n['type'] == 'agent')
    n_anchor = sum(1 for n in data['nodes'] if n['type'] == 'anchor')
    total_plays = data['kpi'].get('total_plays', 0)
    print(f'  錨點:      {n_anchor} (Meta + Shopline)')
    print(f'  業務節點:  {n_agent} (近 {LOOKBACK_DAYS} 天 top {TOP_AGENTS})')
    print(f'  影片節點:  {n_video} (top {TOP_VIDEOS} by plays)')
    print(f'  總節點:    {n_total}')
    print(f'  連線:      {len(data["links"])}')
    print(f'  累計播放:  {total_plays:,}')
    print(f'  UTM 渠道:  {len(data["dataview"]["utm_channels"])} 類')

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
