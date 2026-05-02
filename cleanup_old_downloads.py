#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 data/ 中的舊 shopline_*.xlsx 下載檔
用法：python cleanup_old_downloads.py

策略：保留最新一份 shopline_*.xlsx，其餘刪除。
（封存檔 TZG_YYYY-MM_orders.xlsx / .csv 不會動）
"""
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

def main():
    if not DATA_DIR.exists():
        print(f'[!] {DATA_DIR} 不存在')
        return
    files = sorted(
        DATA_DIR.glob('shopline_*.xlsx'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        print('[cleanup] 沒有 shopline_*.xlsx 檔案')
        return
    keep = files[0]
    print(f'[cleanup] 保留：{keep.name}')
    removed = 0
    for old in files[1:]:
        try:
            old.unlink()
            print(f'[cleanup] 刪除：{old.name}')
            removed += 1
        except Exception as e:
            print(f'[cleanup] 刪除失敗 {old.name}：{e}')
    print(f'[cleanup] 共刪除 {removed} 個舊檔')

if __name__ == '__main__':
    main()
