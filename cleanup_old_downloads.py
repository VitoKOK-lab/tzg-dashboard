#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 data/ 中的舊 shopline_*.xlsx 下載檔
用法：python cleanup_old_downloads.py

策略：依檔名中的 (start, end) 區間分組，每組只保留 mtime 最新的一份。
這樣支援「上月+本月」拆段下載，不會把不同區間的檔案誤刪。
（封存檔 TZG_YYYY-MM_orders.xlsx / .csv 不會動）

檔名格式：shopline_{startYYYYMMDD}_to_{endYYYYMMDD}_{YYYYMMDD}_{HHMMSS}.xlsx
"""
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / 'data'
# 形如 shopline_20260401_to_20260430_20260522_235911.xlsx
PATTERN = re.compile(r'^shopline_(\d{8})_to_(\d{8})_\d{8}_\d{6}\.xlsx$')


def main():
    if not DATA_DIR.exists():
        print(f'[!] {DATA_DIR} 不存在')
        return

    files = list(DATA_DIR.glob('shopline_*.xlsx'))
    if not files:
        print('[cleanup] 沒有 shopline_*.xlsx 檔案')
        return

    # 依 (start, end) 區間分組
    groups = defaultdict(list)
    unmatched = []
    for f in files:
        m = PATTERN.match(f.name)
        if m:
            groups[(m.group(1), m.group(2))].append(f)
        else:
            unmatched.append(f)

    removed = 0
    for key, group in sorted(groups.items()):
        group.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        keep = group[0]
        print(f'[cleanup] 區間 {key[0]}~{key[1]}：保留 {keep.name}')
        for old in group[1:]:
            try:
                old.unlink()
                print(f'[cleanup]                刪除 {old.name}')
                removed += 1
            except Exception as e:
                print(f'[cleanup]                刪除失敗 {old.name}：{e}')

    if unmatched:
        print('[cleanup] 命名不符規則（保留不動）：')
        for f in unmatched:
            print(f'           {f.name}')

    print(f'[cleanup] 共保留 {len(groups)} 個區間檔，刪除 {removed} 個舊檔')


if __name__ == '__main__':
    main()
