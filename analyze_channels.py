#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整通路/業績分析:全通路來源分析 + 業務推廣細項 + 新客舊客拆分 +
消費金額最高前兩名客戶個案追蹤(來源 + 最終付款方式)

延伸自 diagnose_content_flow.py,同樣直接重用 generate_daily.py 的
load_data()/paid_orders()/classify_source() 等函式,不重新寫分類邏輯。

用法:
    python3 analyze_channels.py                  # 全部歷史資料
    python3 analyze_channels.py --month 2026-10   # 只看指定月份
"""
import argparse
import sys

import generate_daily as gd

CCOL = '顧客 ID'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--month', help='指定月份 YYYY-MM，預設全部歷史資料')
    args = ap.parse_args()

    print('載入資料...')
    df = gd.load_data()
    vd = gd.paid_orders(df)

    if args.month:
        yr, mo = map(int, args.month.split('-'))
        s, e = gd.month_range(yr, mo)
        scope_vd = gd.in_range(vd, s, e)
        scope_label = f'{yr}年{mo}月'
    else:
        scope_vd = vd
        scope_label = '全部歷史'

    ord_df = gd.order_level(scope_vd).copy()
    if not len(ord_df):
        print(f'[X] {scope_label} 沒有訂單資料')
        sys.exit(1)

    # 全歷史首購日期(用全部 vd，不受 --month 限制，才能正確判斷新客/回購)
    all_ord = gd.order_level(vd)
    first_order = all_ord.groupby(CCOL)['訂單日期'].min()

    ord_df['_src'] = ord_df.apply(gd.classify_source, axis=1)
    ord_df['_is_new'] = ord_df.apply(
        lambda r: (r[CCOL] in first_order.index) and (r['訂單日期'] == first_order.get(r[CCOL])),
        axis=1
    )

    total_rev = ord_df['訂單合計'].sum()
    print(f'\n{"="*72}')
    print(f' 範圍：{scope_label}　總訂單：{len(ord_df)}　總營收：NT${int(total_rev):,}')
    print(f'{"="*72}\n')

    # ① 全通路來源分析
    print('① 全通路來源分析\n')
    g = ord_df.groupby('_src').agg(
        訂單數=('訂單號碼', 'count'),
        營收=('訂單合計', 'sum'),
        客戶數=(CCOL, 'nunique'),
        新客數=('_is_new', 'sum'),
    ).reset_index().sort_values('營收', ascending=False)
    print(f'{"來源":<14}{"訂單數":>8}{"營收":>14}{"佔比":>8}{"客戶數":>8}{"新客":>8}')
    print('-' * 68)
    for _, r in g.iterrows():
        pct = r['營收'] / total_rev * 100 if total_rev else 0
        print(f'{r["_src"]:<14}{int(r["訂單數"]):>8}{int(r["營收"]):>14,}{pct:>7.1f}%'
              f'{int(r["客戶數"]):>8}{int(r["新客數"]):>8}')

    # ② 業務推廣細項(業務推薦底下，各業務員拆分)
    biz = ord_df[ord_df['_src'] == '業務推薦']
    if len(biz):
        print(f'\n② 業務推廣細項(共 {len(biz)} 筆)\n')
        bg = biz.groupby('推薦活動').agg(
            訂單數=('訂單號碼', 'count'), 營收=('訂單合計', 'sum'),
        ).reset_index().sort_values('營收', ascending=False)
        print(f'{"業務/推薦人":<24}{"訂單數":>8}{"營收":>14}')
        print('-' * 48)
        for _, r in bg.iterrows():
            print(f'{str(r["推薦活動"])[:22]:<24}{int(r["訂單數"]):>8}{int(r["營收"]):>14,}')
    else:
        print('\n② 業務推廣細項：這個範圍內沒有業務推薦訂單')

    # ③ 新客 vs 舊客(回購)總覽
    print('\n③ 新客 vs 舊客(回購)總覽\n')
    new_rev = ord_df[ord_df['_is_new']]['訂單合計'].sum()
    old_rev = ord_df[~ord_df['_is_new']]['訂單合計'].sum()
    new_cnt = int(ord_df['_is_new'].sum())
    old_cnt = len(ord_df) - new_cnt
    if total_rev:
        print(f'  新客：{new_cnt} 筆訂單，NT${int(new_rev):,}（{new_rev/total_rev*100:.1f}%）')
        print(f'  舊客(回購)：{old_cnt} 筆訂單，NT${int(old_rev):,}（{old_rev/total_rev*100:.1f}%）')

    # ④ 消費金額最高前兩名客戶個案追蹤
    print('\n④ 消費金額最高前兩名客戶（個案追蹤：來源 + 每筆付款方式）\n')
    name_col = '顧客' if '顧客' in ord_df.columns else CCOL
    cust_rev = ord_df.groupby(CCOL).agg(
        顧客=(name_col, 'first'), 總營收=('訂單合計', 'sum'), 訂單數=('訂單號碼', 'count'),
    ).reset_index().sort_values('總營收', ascending=False)

    pay_col = '付款方式' if '付款方式' in ord_df.columns else None
    if pay_col is None:
        print('  [!] 資料裡沒有「付款方式」欄位，無法顯示結帳方式')

    for i, (_, r) in enumerate(cust_rev.head(2).iterrows(), 1):
        cid = r[CCOL]
        cust_orders = ord_df[ord_df[CCOL] == cid].sort_values('訂單日期')
        print(f'  第 {i} 名：{r["顧客"]}（共 {int(r["訂單數"])} 筆，總消費 NT${int(r["總營收"]):,}）')
        for _, o in cust_orders.iterrows():
            pay = o[pay_col] if pay_col else '—'
            act = o.get('推薦活動', '')
            act_str = act if act and str(act) != 'nan' else '—'
            print(f'    - {o["訂單日期"].strftime("%Y-%m-%d")}　來源：{o["_src"]}'
                  f'（推薦活動：{act_str}）　付款方式：{pay}　金額：NT${int(o["訂單合計"]):,}')
        print()


if __name__ == '__main__':
    main()
