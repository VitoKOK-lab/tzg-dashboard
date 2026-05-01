#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 月份資料封存  v1.0
======================================================
每月1日自動執行，或手動指定月份：
  python generate_monthly_archive.py
  python generate_monthly_archive.py --month 2026-04
  python generate_monthly_archive.py --month 2026-04 --force

功能：
  - 讀取 data/ 中所有 CSV / XLS / XLSX 檔案
  - 篩選指定月份的訂單（完整欄位，不做標準化截斷）
  - 去重後存成 data/TZG_YYYY-MM_orders.xlsx
  - 已存在則跳過（除非加 --force）
======================================================
"""
import sys
import argparse
import warnings
from pathlib import Path
from datetime import datetime
import pandas as pd

warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / 'data'


def month_range(y, m):
    s = datetime(y, m, 1)
    e = datetime(y + 1, 1, 1) if m == 12 else datetime(y, m + 1, 1)
    return s, e


def load_all_files(data_dir):
    """讀取所有資料檔案，保留完整欄位（不截斷為22欄）"""
    frames = []

    for f in sorted(data_dir.glob('*.csv')):
        # 跳過已封存的月份檔（避免重複讀入）
        if f.name.startswith('TZG_') and '_orders' in f.name:
            try:
                df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False, dtype=str)
                df['_src_file'] = f.name
                frames.append(df)
                print(f'  [CSV] {f.name:55s}  {len(df):>6,} 列')
            except Exception as e:
                print(f'  [!]   {f.name}: {e}')
        else:
            try:
                df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False, dtype=str)
                df['_src_file'] = f.name
                frames.append(df)
                print(f'  [CSV] {f.name:55s}  {len(df):>6,} 列')
            except Exception as e:
                print(f'  [!]   {f.name}: {e}')

    xls_files = sorted(list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.xls')))
    for f in xls_files:
        # 跳過已封存的月份檔
        if f.name.startswith('TZG_') and '_orders' in f.name:
            continue
        try:
            df = pd.read_excel(f, dtype=str)
            df['_src_file'] = f.name
            frames.append(df)
            print(f'  [XLS] {f.name:55s}  {len(df):>6,} 列')
        except Exception as e:
            print(f'  [!]   {f.name}: {e}')

    if not frames:
        print('[X] 沒有找到任何可用的資料檔案')
        return None

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined['訂單日期'] = pd.to_datetime(combined['訂單日期'], errors='coerce')
    combined = combined.dropna(subset=['訂單日期', '訂單號碼']).reset_index(drop=True)

    # 去重：以訂單號碼+商品名稱+選項為鍵，保留最新一筆
    dedup_cols = ['訂單號碼', '商品名稱']
    if '選項' in combined.columns:
        dedup_cols.append('選項')
    combined = combined.drop_duplicates(subset=dedup_cols, keep='last').reset_index(drop=True)

    print(f'\n  [合計] {len(combined):,} 列明細 / {combined["訂單號碼"].nunique():,} 張訂單')
    return combined


def generate_archive(yr, mo, force=False):
    """
    建立 data/TZG_YYYY-MM_orders.xlsx
    回傳檔案路徑，失敗或無資料回傳 None
    """
    out_path = DATA_DIR / f'TZG_{yr}-{mo:02d}_orders.xlsx'

    if out_path.exists() and not force:
        print(f'[已存在] {out_path.name}（若要重建請加 --force 參數）')
        return out_path

    print('讀取所有原始資料...')
    df = load_all_files(DATA_DIR)
    if df is None:
        return None

    s, e = month_range(yr, mo)
    month_df = df[(df['訂單日期'] >= s) & (df['訂單日期'] < e)].copy()
    month_df = month_df.drop(columns=['_src_file'], errors='ignore')

    orders_n = month_df['訂單號碼'].nunique()
    rows_n   = len(month_df)

    if rows_n == 0:
        print(f'[!] {yr}年{mo}月 沒有資料，不建立封存檔')
        return None

    print(f'\n[封存資料] {yr}年{mo}月')
    print(f'  訂單數：{orders_n:,} 張')
    print(f'  明細列：{rows_n:,} 列')
    print(f'  欄位數：{len(month_df.columns)} 欄')

    month_df.to_excel(out_path, index=False, engine='openpyxl')
    size_kb = out_path.stat().st_size // 1024
    print(f'\n[✓] 已儲存：{out_path.name}  ({size_kb:,} KB)')
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description='TZG 月份資料封存工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='範例：\n  python generate_monthly_archive.py\n  python generate_monthly_archive.py --month 2026-04\n  python generate_monthly_archive.py --month 2026-04 --force'
    )
    parser.add_argument('--month', type=str, metavar='YYYY-MM',
                        help='指定月份（預設：上個月）')
    parser.add_argument('--force', action='store_true',
                        help='覆蓋已存在的封存檔')
    args = parser.parse_args()

    if args.month:
        try:
            dt = datetime.strptime(args.month, '%Y-%m')
            yr, mo = dt.year, dt.month
        except ValueError:
            print(f'[X] 格式錯誤：{args.month}，請使用 YYYY-MM（例：2026-04）')
            sys.exit(1)
    else:
        now = datetime.now()
        yr  = now.year - 1 if now.month == 1 else now.year
        mo  = 12          if now.month == 1 else now.month - 1

    print('=' * 60)
    print(f'  TZG 月份封存  →  {yr}年{mo:02d}月')
    print('=' * 60)
    print()

    result = generate_archive(yr, mo, force=args.force)

    print()
    if result:
        print('=' * 60)
        print('  [完成] 封存成功')
        print(f'         {result.name}')
        print('=' * 60)
    else:
        print('[失敗] 封存未完成')
        sys.exit(1)


if __name__ == '__main__':
    main()
