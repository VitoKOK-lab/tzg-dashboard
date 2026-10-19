#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 電商日報 — 手機優先版 v2（測試用，跟舊版並存，不影響正式版）

重用 generate_daily.py 的 load_data() / compute() / patch_html()，
只是換一份全新、手機優先排版的模板，輸出到 output/dashboard_v2.html。
舊版 dashboard_latest.html 完全不受影響。

用法：
    python3 generate_daily_v2.py
"""
import sys
import traceback
from pathlib import Path
from datetime import datetime

import generate_daily as gd

TEMPLATE_HTML = Path('./data/templates/dashboard_mobile_v2.html')
OUTPUT_DIR = Path('./output')
OUTPUT_V2 = OUTPUT_DIR / 'dashboard_v2.html'


def main():
    print('=' * 70)
    print(' 🎯 TZG 電商日報 — 手機優先版 v2（測試用，不影響正式版）')
    print('=' * 70)

    OUTPUT_DIR.mkdir(exist_ok=True)

    print('\n[步驟 1/3] 加載數據...')
    df = gd.load_data()

    print('\n[步驟 2/3] 計算指標...')
    try:
        D = gd.compute(df)
        print('[✓] 指標計算完成（跟舊版用同一套計算邏輯）')
    except Exception as e:
        print(f'[✗] 計算失敗：{e}')
        traceback.print_exc()
        sys.exit(1)

    print('\n[步驟 3/3] 生成 HTML...')
    if not TEMPLATE_HTML.exists():
        print(f'[✗] 找不到模板：{TEMPLATE_HTML}')
        sys.exit(1)

    html = TEMPLATE_HTML.read_text(encoding='utf-8')
    try:
        new_html = gd.patch_html(html, D)

        last_update_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_html = new_html.replace('__LAST_UPDATE__', last_update_str)

        # 資料新鮮度：跟舊版同樣邏輯，用「最後一筆訂單實際時刻」判斷
        data_as_of_str = D['meta']['data_as_of']
        data_as_of_iso = D['meta'].get('data_as_of_iso')
        if data_as_of_iso:
            last_order_dt = datetime.strptime(data_as_of_iso, '%Y-%m-%dT%H:%M:%S')
        else:
            last_order_dt = datetime.strptime(data_as_of_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        stale_hours = max(0, (datetime.now() - last_order_dt).total_seconds() / 3600)
        stale_class = 'stale' if stale_hours > 24 else ''
        new_html = new_html.replace('__STALE_CLASS__', stale_class)
        if stale_hours > 24:
            print(f'[⚠️ ] 資料停滯 {int(stale_hours)} 小時，topbar 已標示橘色過期警示')
        else:
            print(f'[✓] 資料新鮮（停滯 {stale_hours:.1f} 小時 < 24h）')

        print(f'[✓] 數據注入完成：{len(new_html):,} 字元')
    except Exception as e:
        print(f'[✗] 數據注入失敗：{e}')
        traceback.print_exc()
        sys.exit(1)

    OUTPUT_V2.write_text(new_html, encoding='utf-8')
    print(f'[✓] 輸出：{OUTPUT_V2}')

    print('\n' + '=' * 70)
    print('[✅ 成功] 手機優先版 v2 已生成，正式版 dashboard_latest.html 完全不受影響')
    print(f'  本地打開測試：open {OUTPUT_V2}')
    print('=' * 70)


if __name__ == '__main__':
    main()
