#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 測試儀表板 — Cyberpunk 神經中樞 v0.1
============================================================
獨立的測試環境，不影響原本日/月報流程、不接 LaunchAgent、不進主流程.sh。

產出：output/test.html（單一靜態檔，可直接打開）
資料：從 generate_daily 的 load_data 讀近 90 天有效訂單

節點 = 業務（推薦活動）
大小 = 業績
顏色 = 業績層級（粉/紫/青）
連線 = 共享客戶數量 ≥ 2

用法：
  python3 generate_test.py
線上路徑：
  https://vitokok-lab.github.io/tzg-dashboard/output/test.html
============================================================
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from itertools import combinations

sys.path.insert(0, '.')
from generate_daily import load_data, paid_orders, is_real_agent

OUTPUT_HTML = Path('./output/test.html')
TEMPLATE_HTML = Path('./data/templates/test_template.html')
LOOKBACK_DAYS = 90
TOP_N_AGENTS = 30


def build_graph_data():
    df = load_data()
    vd = paid_orders(df)

    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    vd = vd[vd['訂單日期'] >= cutoff]
    if len(vd) == 0 or '推薦活動' not in vd.columns:
        return {'nodes': [], 'links': [], 'kpi': {'period_label': f'近 {LOOKBACK_DAYS} 天'}}

    ccol = '顧客 ID' if '顧客 ID' in vd.columns else '顧客'
    vd_ag = vd[vd['推薦活動'].notna() & vd['推薦活動'].apply(is_real_agent)]
    if len(vd_ag) == 0:
        return {'nodes': [], 'links': [], 'kpi': {'period_label': f'近 {LOOKBACK_DAYS} 天'}}

    ord_lvl = vd_ag.drop_duplicates('訂單號碼')
    agg = ord_lvl.groupby('推薦活動').agg(
        orders=('訂單號碼', 'count'),
        rev=('訂單合計', 'sum'),
        customers=(ccol, 'nunique'),
    ).reset_index().sort_values('rev', ascending=False).head(TOP_N_AGENTS)

    nodes = []
    for _, r in agg.iterrows():
        name = str(r['推薦活動'])
        display = name.split('/')[0].strip() if '/' in name else name
        if len(display) > 10:
            display = display[:10]
        location = ''
        parts = [p.strip() for p in name.split('/') if p.strip()]
        if len(parts) >= 3:
            location = parts[-1]
        nodes.append({
            'id': name,
            'name': display,
            'fullName': name,
            'location': location,
            'rev': int(r['rev']),
            'orders': int(r['orders']),
            'customers': int(r['customers']),
            'aov': int(r['rev'] / r['orders']) if r['orders'] else 0,
        })

    agent_set = set(n['id'] for n in nodes)
    vd_top = vd_ag[vd_ag['推薦活動'].isin(agent_set)]
    cust_agents = (
        vd_top.drop_duplicates(['訂單號碼'])
              .groupby(ccol)['推薦活動']
              .apply(lambda s: set(s.dropna()))
    )

    pair_count = {}
    for _, ag_set in cust_agents.items():
        if len(ag_set) > 1:
            for a, b in combinations(sorted(ag_set), 2):
                pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    links = [
        {'source': a, 'target': b, 'value': v}
        for (a, b), v in pair_count.items() if v >= 2
    ]

    total_ord = vd.drop_duplicates('訂單號碼')
    kpi = {
        'total_rev': int(total_ord['訂單合計'].sum()),
        'total_orders': int(len(total_ord)),
        'total_customers': int(vd[ccol].nunique()),
        'avg_aov': int(total_ord['訂單合計'].mean()) if len(total_ord) else 0,
        'top_agents': nodes[:6],
        'period_label': f'近 {LOOKBACK_DAYS} 天',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    return {'nodes': nodes, 'links': links, 'kpi': kpi}


def main():
    print('=' * 60)
    print(' 🧠 TZG 測試儀表板 - 神經中樞 v0.1')
    print('=' * 60)

    print('\n[1/3] 載入資料...')
    data = build_graph_data()
    n_nodes = len(data['nodes'])
    n_links = len(data['links'])
    kpi = data['kpi']
    print(f'  業務節點: {n_nodes}')
    print(f'  連線（共享客戶 ≥2）: {n_links}')
    if 'total_rev' in kpi:
        print(f'  中央 KPI: NT$ {kpi["total_rev"]:,} / '
              f'{kpi["total_orders"]} 訂單 / {kpi["total_customers"]} 客戶')

    print('\n[2/3] 載入模板...')
    if not TEMPLATE_HTML.exists():
        print(f'[✗] 找不到模板：{TEMPLATE_HTML}')
        sys.exit(1)
    html = TEMPLATE_HTML.read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False, default=str)
    html = html.replace('__GRAPH_DATA__', payload)

    print('\n[3/3] 寫檔...')
    OUTPUT_HTML.parent.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding='utf-8')
    size_kb = OUTPUT_HTML.stat().st_size // 1024
    print(f'[✓] 已生成：{OUTPUT_HTML}  ({size_kb} KB)')
    print()
    print('  本機預覽：')
    print(f'    open {OUTPUT_HTML}')
    print('  GitHub Pages 上線：')
    print('    https://vitokok-lab.github.io/tzg-dashboard/output/test.html')
    print()


if __name__ == '__main__':
    main()
