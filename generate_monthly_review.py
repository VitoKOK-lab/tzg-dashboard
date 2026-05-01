#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 月會專用網頁產生器  v1.0
==============================================================
產出：output/monthly_review.html
含所有有資料的月份，使用者可在頁面下拉選單切換查看

每月1日由排程自動執行。
==============================================================
"""
import sys
import json
import warnings
import calendar as _cal
from pathlib import Path
from datetime import datetime

# 從 generate_daily 引入共用函數
from generate_daily import (
    load_data, paid_orders, compute_month_review,
    DATA_DIR, MONTHLY_TARGET,
)

warnings.filterwarnings('ignore')

OUTPUT_DIR    = Path('./output')
OUTPUT_HTML   = OUTPUT_DIR / 'monthly_review.html'
TEMPLATE_HTML = Path('./data/templates/monthly_review_template.html')


def find_months_with_data(vd):
    """找出資料中有訂單的所有 (year, month) 組合"""
    if len(vd) == 0:
        return []
    ym = vd['訂單日期'].dt.to_period('M').unique()
    months = sorted([(p.year, p.month) for p in ym])
    return months


def _replace_object_after(html, marker, new_obj):
    """把 html 裡 marker 後面的 JS 物件 {...} 換成 new_obj 的 JSON"""
    idx = html.find(marker)
    if idx < 0:
        return html  # 找不到 marker 直接返回
    start = html.find('{', idx)
    depth, in_str, esc = 0, False, False
    end, i = None, start
    while i < len(html):
        c = html[i]
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': in_str = not in_str
        elif not in_str:
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    if end is None:
        return html
    new_json = json.dumps(new_obj, ensure_ascii=False, default=str)
    return html[:start] + new_json + html[end:]


def patch_html(html, all_data, annual_plan):
    """注入 ALL_DATA 和 ORIGINAL_PLAN"""
    html = _replace_object_after(html, 'const ALL_DATA=',      all_data)
    html = _replace_object_after(html, 'const ORIGINAL_PLAN=', annual_plan)
    return html


def main():
    print('=' * 70)
    print('  📊 TZG 月會專用網頁產生器  v1.0')
    print('=' * 70)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. 讀取資料
    print('\n[1/3] 載入資料...')
    df = load_data()
    vd = paid_orders(df)
    ccol = '顧客 ID'
    print(f'  有效訂單 {vd["訂單號碼"].nunique():,} 張，'
          f'日期 {vd["訂單日期"].min():%Y-%m-%d} ~ {vd["訂單日期"].max():%Y-%m-%d}')

    # 2. 找出所有月份並計算
    print('\n[2/3] 計算各月回顧...')
    months = find_months_with_data(vd)

    # 只列出「已完整結束」的月份：
    #   - 月份 (y, m) 必須整月過完 → 即 (y, m) < (今天年, 今天月)
    #   - 範圍限縮在當年（1 月時補入去年 12 月）
    today        = datetime.now()
    target_year  = today.year
    months_to_show = [
        (y, m) for y, m in months
        if y == target_year and (y, m) < (target_year, today.month)
    ]
    if today.month == 1 and (target_year - 1, 12) in months:
        months_to_show.insert(0, (target_year - 1, 12))

    if not months_to_show:
        print('[!] 目前沒有任何「已結束」的月份可以列出')
        print('    （月會頁面要等月份完整結束才會產生）')

    all_data = {}
    for yr, mo in months_to_show:
        review = compute_month_review(vd, ccol, yr, mo)
        if review:
            key = f'{yr}-{mo:02d}'
            all_data[key] = review
            print(f'  [✓] {key}  · NT${review["rev"]:>10,} / {review["orders"]:>4}張 · 達成 {review["achievement_pct"]:>5.1f}%')

    if not all_data:
        print('[X] 沒有任何月份的資料可以產出')
        sys.exit(1)

    print(f'\n  共產出 {len(all_data)} 個月份')

    # 3. 套版輸出
    print('\n[3/3] 載入模板並注入資料...')
    if not TEMPLATE_HTML.exists():
        print(f'[X] 找不到模板：{TEMPLATE_HTML}')
        sys.exit(1)

    # 載入年度業績目標檔（給設定頁使用）
    annual_plan = {}
    plan_path = Path('./annual_plan.json')
    if plan_path.exists():
        try:
            annual_plan = json.loads(plan_path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'  [!] annual_plan.json 解析失敗：{e}')

    html = TEMPLATE_HTML.read_text(encoding='utf-8')
    new_html = patch_html(html, all_data, annual_plan)
    OUTPUT_HTML.write_text(new_html, encoding='utf-8')

    size_kb = OUTPUT_HTML.stat().st_size // 1024
    print(f'  [✓] 已生成：{OUTPUT_HTML}  ({size_kb:,} KB)')

    print('\n' + '=' * 70)
    print('  [✅ 成功] 月會網頁已生成')
    print('=' * 70)
    print(f'\n  上傳檔案：{OUTPUT_HTML}')
    print(f'  GitHub Pages 上線位置：')
    print(f'    https://vitokok-lab.github.io/tzg-dashboard/output/monthly_review.html')
    print()


if __name__ == '__main__':
    main()
