#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷工具：「內容導流」底下的「推薦活動」欄位實際填了什麼

「內容導流」是 generate_daily.py::classify_ad_channel() 的預設分類——
「推薦活動」欄位有填值、但辨識不出屬於哪個已知平台(LINE/FB/IG/TikTok/
YouTube/Threads)的訂單，全部會被歸進這一類。這個腳本把這些訂單的
「推薦活動」欄位值抓出來，依出現次數排序，讓你看清楚具體是哪些代碼/
文案撐出了這個分類的佔比。

用法：
    python3 diagnose_content_flow.py                  # 預設：當月
    python3 diagnose_content_flow.py --month 2026-10   # 指定月份
    python3 diagnose_content_flow.py --all             # 全部歷史資料(不分月)
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

import generate_daily as gd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--month', help='指定月份 YYYY-MM，預設當月')
    ap.add_argument('--all', action='store_true', help='不分月份，看全部歷史資料')
    args = ap.parse_args()

    print('載入資料...')
    df = gd.load_data()
    vd = gd.paid_orders(df)

    if args.all:
        scope_df = vd
        scope_label = '全部歷史'
    else:
        if args.month:
            yr, mo = map(int, args.month.split('-'))
        else:
            now = datetime.now()
            yr, mo = now.year, now.month
        s, e = gd.month_range(yr, mo)
        scope_df = gd.in_range(vd, s, e)
        scope_label = f'{yr}年{mo}月'

    ord_df = gd.order_level(scope_df).copy()
    if not len(ord_df):
        print(f'[X] {scope_label} 沒有訂單資料')
        sys.exit(1)

    ord_df['_src'] = ord_df.apply(gd.classify_source, axis=1)
    content_flow = ord_df[ord_df['_src'] == '內容導流']

    total_orders = len(ord_df)
    cf_orders = len(content_flow)
    print(f'\n{"="*60}')
    print(f' 範圍：{scope_label}')
    print(f' 總訂單數：{total_orders}　內容導流：{cf_orders}　'
          f'({cf_orders/total_orders*100:.1f}%)' if total_orders else '')
    print(f'{"="*60}\n')

    if not cf_orders:
        print('這個範圍內沒有被分類成「內容導流」的訂單。')
        return

    g = content_flow.groupby('推薦活動').agg(
        訂單數=('訂單號碼', 'count'),
        營收=('訂單合計', 'sum'),
    ).reset_index().sort_values('訂單數', ascending=False)

    print(f'「推薦活動」欄位值分布(共 {len(g)} 種不同值)：\n')
    print(f'{"推薦活動內容":<40}{"訂單數":>8}{"營收":>14}')
    print('-' * 62)
    for _, r in g.iterrows():
        val = str(r['推薦活動'])[:38]
        print(f'{val:<40}{int(r["訂單數"]):>8}{int(r["營收"]):>14,}')

    out_path = Path(f'output/content_flow_{scope_label.replace("年","-").replace("月","")}.csv')
    out_path.parent.mkdir(exist_ok=True)
    g.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'\n[✓] 完整清單已存到 {out_path}(可以用 Excel 打開)')


if __name__ == '__main__':
    main()
