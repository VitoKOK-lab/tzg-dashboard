#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopline 請求錄製工具
執行後：你手動登入，點一次匯出鍵，腳本自動記錄 API 請求
結果存至：shopline_api_log.txt
"""
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

EMAIL    = os.getenv('SHOPLINE_EMAIL', '')
PASSWORD = os.getenv('SHOPLINE_PASSWORD', '')

SHOP_ID    = 'tzgrotw251'
LOGIN_URL  = f'https://admin.shoplineapp.com/admin/{SHOP_ID}'
REPORT_URL = f'https://admin.shoplineapp.com/admin/{SHOP_ID}/reports/orders_by_product'
LOG_FILE   = Path('shopline_api_log.txt')

captured = []

def on_request(request):
    url = request.url
    # 只記錄可能是匯出的請求（CSV / export / download）
    keywords = ['export', 'download', 'csv', 'report', 'xlsx', 'orders']
    if any(k in url.lower() for k in keywords):
        entry = {
            'time':    datetime.now().strftime('%H:%M:%S'),
            'method':  request.method,
            'url':     url,
            'headers': dict(request.headers),
            'body':    request.post_data or '',
        }
        captured.append(entry)
        print(f'\n🎯 攔截到請求！')
        print(f'   方法：{request.method}')
        print(f'   URL ：{url}')
        if request.post_data:
            print(f'   Body：{request.post_data[:200]}')

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(accept_downloads=True)
        page    = context.new_page()

        # 監聽所有請求
        page.on('request', on_request)

        print('=' * 60)
        print(' Shopline 請求錄製工具')
        print('=' * 60)

        if EMAIL and PASSWORD:
            # 自動登入
            print('\n[1] 自動登入中...')
            page.goto(LOGIN_URL, wait_until='networkidle', timeout=30000)

            try:
                page.wait_for_selector(
                    'input[type="email"], input[name="email"]',
                    timeout=10000
                )
                page.locator('input[type="email"], input[name="email"]').first.fill(EMAIL)
                page.locator('input[type="password"]').first.fill(PASSWORD)
                page.locator('button[type="submit"], input[type="submit"]').first.click()
                page.wait_for_url(f'**/admin/{SHOP_ID}/**', timeout=30000)
                print('[✓] 登入成功')
            except Exception as e:
                print(f'[!] 自動登入失敗：{e}')
                print('    請在瀏覽器視窗手動登入')
        else:
            print('\n[1] 請在瀏覽器視窗手動登入...')
            page.goto(LOGIN_URL)

        # 前往報表頁
        print(f'\n[2] 前往報表頁：{REPORT_URL}')
        page.goto(REPORT_URL, wait_until='networkidle', timeout=30000)

        # 截圖記錄頁面狀態
        page.screenshot(path='discover_report_page.png', full_page=True)
        print('[✓] 截圖已存：discover_report_page.png')

        # 列出頁面上所有按鈕和連結
        print('\n[3] 掃描頁面上的按鈕和連結：')
        elements = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('button, a, [role="button"], [class*="export"], [class*="download"]').forEach(el => {
                const text = (el.innerText || el.textContent || '').trim().slice(0, 80);
                const cls  = el.className || '';
                const href = el.href || '';
                if (text || href) {
                    results.push({
                        tag:  el.tagName,
                        text: text,
                        cls:  cls.slice(0, 80),
                        href: href.slice(0, 100),
                    });
                }
            });
            return results;
        }""")

        for el in elements:
            label = el['text'] or el['href']
            if label:
                print(f"  [{el['tag']}] {label[:60]}  class={el['cls'][:40]}")

        print('\n' + '='*60)
        print('👆 請現在在瀏覽器裡：')
        print('   1. 設定好日期範圍')
        print('   2. 點擊「匯出」或「Export」按鈕')
        print('   3. 如有彈窗，繼續點確認匯出')
        print('='*60)
        print('\n（操作完成後按 Enter 結束錄製）')
        input()

        # 存結果
        LOG_FILE.write_text(
            json.dumps(captured, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'\n[✓] 錄製完成！共攔截 {len(captured)} 個相關請求')
        print(f'[✓] 結果存至：{LOG_FILE}')

        if not captured:
            print('\n[!] 沒有攔截到匯出請求')
            print('    可能原因：')
            print('    1. 匯出是純前端下載（沒有 API 請求）')
            print('    2. 關鍵字不符（嘗試調整 keywords 清單）')
            print('    3. 你尚未點擊匯出按鈕')
            print('\n    已截圖頁面：discover_report_page.png')

        browser.close()

if __name__ == '__main__':
    run()
