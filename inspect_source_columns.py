#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 Shopline 原始匯出檔裡的來源相關欄位實際填了什麼

generate_daily.py::load_data() 只保留 22 個標準欄位,UTM、導購來源平台、
銷售人員等欄位都被丟掉。這支直接讀 data/ 裡的原始 .xlsx,看這些欄位
的填寫率與常見值,以及「推薦活動沒填」(目前被歸成直接/官網)的訂單
UTM 實際是什麼,決定之後分析能不能改用 UTM 判斷來源。

用法:
    python3 inspect_source_columns.py
"""
from pathlib import Path

import pandas as pd

COLS = ['UTM 來源', 'UTM 媒介', 'UTM 活動名稱', 'UTM 活動內容', '導購來源平台',
        '訂單來源類型', '銷售人員', '會員註冊來源', '合作夥伴', '推薦人姓名']


def load_raw(data_dir=Path('data')):
    dfs = []
    for f in sorted(data_dir.glob('*.xlsx')):
        try:
            df = pd.read_excel(f, dtype=str)
        except Exception as e:
            print(f'  [跳過] {f.name}:{e}')
            continue
        if '訂單號碼' not in df.columns or 'UTM 來源' not in df.columns:
            continue
        dfs.append(df)
    if not dfs:
        return None
    raw = pd.concat(dfs, ignore_index=True)
    # 同一張訂單會出現在多個累積下載檔和多個商品列,只留一列
    ords = raw.drop_duplicates('訂單號碼', keep='last').copy()
    ords['訂單合計'] = pd.to_numeric(ords['訂單合計'], errors='coerce').fillna(0)
    return ords


def blank(s):
    return s.isna() | s.astype(str).str.strip().isin(['', 'nan', 'None'])


def top_values(ords, col, n=15):
    s = ords[col]
    filled = ~blank(s)
    g = (ords[filled].groupby(col)
         .agg(訂單數=('訂單號碼', 'count'), 營收=('訂單合計', 'sum'))
         .sort_values('訂單數', ascending=False).head(n))
    return int(filled.sum()), g


def main():
    print('讀取 data/ 裡含 UTM 欄位的原始 .xlsx...')
    ords = load_raw()
    if ords is None:
        print('[X] 找不到含「UTM 來源」欄位的 .xlsx 檔')
        return
    total = len(ords)
    dates = pd.to_datetime(ords['訂單日期'], errors='coerce')
    print(f'\n共 {total:,} 張訂單(訂單日期 {dates.min():%Y-%m-%d} ~ {dates.max():%Y-%m-%d})\n')

    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 200)
    fmt = {'營收': '{:,.0f}'.format}

    print('=' * 60)
    print(' ① 各欄位填寫率')
    print('=' * 60)
    for col in COLS:
        if col not in ords.columns:
            print(f'  {col:<12} (檔案裡沒有這欄)')
            continue
        n = int((~blank(ords[col])).sum())
        print(f'  {col:<12} {n:>7,} 張 ({n/total*100:5.1f}%)')

    for col in COLS:
        if col not in ords.columns:
            continue
        n, g = top_values(ords, col)
        if not n:
            continue
        print(f'\n── {col} 常見值(前 15) ──')
        print(g.to_string(formatters=fmt))

    no_act = ords[blank(ords['推薦活動'])]
    print('\n' + '=' * 60)
    print(f' ② 推薦活動沒填的訂單({len(no_act):,} 張,目前多半被歸成直接/官網)')
    print('    它們的 UTM 實際是什麼')
    print('=' * 60)
    for col in ['UTM 來源', 'UTM 媒介']:
        n, g = top_values(no_act, col)
        print(f'\n── {col}:有填 {n:,} 張 ({n/len(no_act)*100 if len(no_act) else 0:.1f}%) ──')
        if n:
            print(g.to_string(formatters=fmt))


if __name__ == '__main__':
    main()
