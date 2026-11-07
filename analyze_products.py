#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材該推哪個商品:入門商品的客人價值 + 第一單→第二單的升級路徑

回答兩件事:
  ① 哪個「入門商品」帶進來的新客,首購後 90 天最會回購、花最多(拉新素材該推什麼)
  ② 回購客人實際發生過的「第一單主商品 → 第二單主商品」路徑(升級素材 / LINE 圖庫該推什麼)
「主商品」= 那張訂單裡金額最高的真實商品(排除禮盒、包裝、運費等)。

用法:
    python3 analyze_products.py               # 入門商品至少 20 位新客才列入
    python3 analyze_products.py --min 10
"""
import argparse
from pathlib import Path

import pandas as pd

import generate_daily as gd

CCOL = '顧客 ID'
# 不用 gd.is_real_product:它為組合分析設計,會排除「訂製/客製化」和熱賣的消磁聚寶盆,
# 但訂製正是要找的升級目標。這裡只排除不是商品的項目。
NOT_PRODUCT = ['禮盒', '包裝', '贈品', '運費', '試戴', '改圍', '補差價', '手工費', '補貼',
               '加工', '維修', '保養', '鑑定', '證書', '放大鏡', '1元下單', '下單專區']


def is_product(name):
    n = str(name)
    return n not in ('', 'nan') and not any(k in n for k in NOT_PRODUCT)


def main_products(lines):
    """每張訂單取金額最高的商品當主商品。"""
    lines = lines[lines['商品名稱'].map(is_product)].copy()
    lines['_amt'] = lines['商品結帳價'].fillna(0) * lines['數量'].fillna(1)
    idx = lines.sort_values('_amt', ascending=False).drop_duplicates('訂單號碼').index
    return lines.loc[idx].set_index('訂單號碼')['商品名稱']


def build(vd, min_customers):
    ords = gd.order_level(vd)[['訂單號碼', CCOL, '訂單日期', '訂單合計']].dropna(subset=[CCOL])
    ords = ords.sort_values('訂單日期')
    ords['_main'] = ords['訂單號碼'].map(main_products(vd))
    ords['_seq'] = ords.groupby(CCOL).cumcount() + 1

    first = ords[ords['_seq'] == 1].set_index(CCOL)
    cutoff = ords['訂單日期'].max() - pd.Timedelta(days=90)
    mature = first[(first['訂單日期'] <= cutoff) & first['_main'].notna()]
    rows = ords[ords[CCOL].isin(mature.index)]
    win = rows[rows['訂單日期'] <= rows[CCOL].map(mature['訂單日期']) + pd.Timedelta(days=90)]
    cust = pd.DataFrame({
        '入門商品': mature['_main'],
        '首單金額': mature['訂單合計'],
        '90天營收': win.groupby(CCOL)['訂單合計'].sum(),
        '90天筆數': win.groupby(CCOL)['訂單號碼'].count(),
    })
    t1 = cust.groupby('入門商品').agg(
        新客數=('首單金額', 'size'),
        首單中位數=('首單金額', 'median'),
        九十天營收中位數=('90天營收', 'median'),
        九十天平均營收=('90天營收', 'mean'),
        回購率=('90天筆數', lambda s: (s > 1).mean() * 100),
    )
    t1 = t1[t1['新客數'] >= min_customers].round(1)
    t1 = t1.sort_values(['回購率', '九十天營收中位數'], ascending=False)

    second = ords[ords['_seq'] == 2].set_index(CCOL)
    pair = pd.DataFrame({'第一單': first['_main'], '第二單': second['_main'],
                         '第二單金額': second['訂單合計']}).dropna(subset=['第一單', '第二單'])
    t2 = pair.groupby(['第一單', '第二單']).agg(
        人數=('第二單金額', 'size'), 第二單金額中位數=('第二單金額', 'median'),
    ).reset_index().sort_values(['人數', '第二單金額中位數'], ascending=False)
    t2 = t2[t2['人數'] >= 2]
    t3 = t2.sort_values('第二單金額中位數', ascending=False)
    return t1, t2, t3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min', type=int, default=20, help='入門商品至少幾位新客才列入(預設 20)')
    args = ap.parse_args()

    print('載入資料...')
    vd = gd.paid_orders(gd.load_data())
    t1, t2, t3 = build(vd, args.min)

    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 220)
    pd.set_option('display.max_colwidth', 40)
    money = '{:,.0f}'.format

    print(f'\n① 入門商品的新客價值(新客 ≥{args.min} 位、首購滿 90 天;依回購率排序)\n')
    print('  拉新素材優先推「回購率高 + 90天營收中位數高」的商品,不是新客最多的\n')
    print(t1.head(40).to_string(formatters={'首單中位數': money, '九十天營收中位數': money,
                                            '九十天平均營收': money}))
    print('\n② 最常發生的升級路徑(第一單主商品 → 第二單主商品,至少 2 人)\n')
    print(t2.head(30).to_string(index=False, formatters={'第二單金額中位數': money}))
    print('\n③ 第二單金額最高的路徑(至少 2 人;升級素材 / LINE 圖庫優先做這些)\n')
    print(t3.head(20).to_string(index=False, formatters={'第二單金額中位數': money}))

    out = Path('output')
    out.mkdir(exist_ok=True)
    t1.to_csv(out / 'products_entry.csv', encoding='utf-8-sig')
    t2.to_csv(out / 'products_paths.csv', index=False, encoding='utf-8-sig')
    print('\n[✓] 完整清單已存 output/products_entry.csv、output/products_paths.csv')


if __name__ == '__main__':
    main()
