#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 重新封存月份  v1.0
==============================================================
從 Shopline 重新下載指定月份的最新資料 → 取代舊封存
解決：跨月取消／退款 沒有反映在舊資料的問題

用法：
  python re_archive_month.py --month 2026-03
  python re_archive_month.py --months 2026-01,2026-02,2026-03    # 一次處理多個月

效果：
  1. 從 Shopline 下載該月最新訂單（含當前 付款狀態 / 訂單狀態）
  2. 覆蓋舊的 TZG_YYYY-MM_orders.xlsx
  3. 刪除已被取代的舊 CSV（如果存在）
==============================================================
"""
import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'


def re_archive(yr, mo):
    print()
    print('━' * 60)
    print(f'  開始重新封存：{yr}年{mo:02d}月')
    print('━' * 60)
    print()

    # Step 1: 從 Shopline 下載最新月份資料
    target = f'{yr}-{mo:02d}'
    print(f'[1/3] 從 Shopline 下載 {target} 整月資料...')
    print(f'      （瀏覽器會打開，請勿關閉）')
    print()

    result = subprocess.run(
        [sys.executable, 'auto_shopline.py', '--month', target],
        cwd=str(Path(__file__).parent),
    )
    if result.returncode != 0:
        print(f'[X] Shopline 下載失敗')
        return False

    print()
    print(f'[2/3] 重建封存檔 TZG_{target}_orders.xlsx ...')

    # Step 2: 強制重建封存
    result = subprocess.run(
        [sys.executable, 'generate_monthly_archive.py', '--month', target, '--force'],
        cwd=str(Path(__file__).parent),
    )
    if result.returncode != 0:
        print(f'[X] 封存重建失敗')
        return False

    # Step 3: 刪除舊 CSV（若存在）
    print()
    print(f'[3/3] 清理舊檔案...')
    old_csv = DATA_DIR / f'TZG_{target}_orders.csv'
    if old_csv.exists():
        old_csv.unlink()
        print(f'      已刪除舊 CSV：{old_csv.name}')
    else:
        print(f'      （無舊 CSV）')

    # 刪除剛下載的 shopline_*.xlsx（已合併到封存檔）
    pattern = f'shopline_{yr}{mo:02d}*_to_{yr}{mo:02d}*.xlsx'
    for f in DATA_DIR.glob(pattern):
        f.unlink()
        print(f'      已刪除暫存：{f.name}')

    print()
    print(f'[✓] {yr}年{mo}月 重新封存完成')
    return True


def main():
    parser = argparse.ArgumentParser(description='TZG 月份重新封存')
    parser.add_argument('--month',  type=str, metavar='YYYY-MM',
                        help='重新封存單一月份（例：2026-03）')
    parser.add_argument('--months', type=str, metavar='YYYY-MM,...',
                        help='重新封存多個月份（逗號分隔，例：2026-01,2026-02,2026-03）')
    args = parser.parse_args()

    months = []
    if args.months:
        for m in args.months.split(','):
            try:
                dt = datetime.strptime(m.strip(), '%Y-%m')
                months.append((dt.year, dt.month))
            except ValueError:
                print(f'[X] 格式錯誤：{m}')
                sys.exit(1)
    elif args.month:
        try:
            dt = datetime.strptime(args.month, '%Y-%m')
            months.append((dt.year, dt.month))
        except ValueError:
            print(f'[X] 格式錯誤：{args.month}')
            sys.exit(1)
    else:
        # 預設：重新封存「上 1 個月」
        # （catch 月底下載漏抓 + 跨月退款 / 取消）
        now = datetime.now()
        yr, mo = now.year, now.month - 1
        if mo <= 0:
            mo += 12
            yr -= 1
        months.append((yr, mo))

    print('=' * 60)
    print(f'  TZG 月份重新封存')
    print(f'  目標月份：{", ".join(f"{y}-{m:02d}" for y, m in months)}')
    print('=' * 60)

    success_count = 0
    for yr, mo in months:
        if re_archive(yr, mo):
            success_count += 1
        # 兩個月份之間休息 5 秒，避免 Shopline 連續登入造成阻擋
        if (yr, mo) != months[-1]:
            print('\n  休息 5 秒...\n')
            time.sleep(5)

    print()
    print('=' * 60)
    print(f'  完成：{success_count}/{len(months)} 個月份成功')
    print('=' * 60)


if __name__ == '__main__':
    main()
