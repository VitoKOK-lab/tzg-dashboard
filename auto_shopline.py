#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopline 自動下載訂單報表 v3.1
- Session 儲存：登入一次，之後自動重用
- 支援 Google Authenticator 2FA（手動登入後不再需要）
- 正確選擇器：a.export-item
- 🆕 支援指定日期範圍：
    python auto_shopline.py                       # 預設：當月 1 號 ~ 今天
    python auto_shopline.py --month 2026-03       # 整個 3 月
    python auto_shopline.py --start 2026-01-01 --end 2026-01-31
"""
import os
import sys
import json
import argparse
import calendar as _cal
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

EMAIL    = os.getenv('SHOPLINE_EMAIL', '')
PASSWORD = os.getenv('SHOPLINE_PASSWORD', '')

SHOP_ID      = 'tzgrotw251'
LOGIN_URL    = f'https://admin.shoplineapp.com/admin/{SHOP_ID}'
REPORT_URL   = f'https://admin.shoplineapp.com/admin/{SHOP_ID}/reports/orders_by_product'
DATA_DIR     = Path('./data')
SESSION_FILE = Path('./shopline_session.json')   # 儲存登入 Session

# 第一次測試用 False（看得見）；確認OK後改 True（背景執行）
# 排程模式可用環境變數 TZG_HEADLESS=1 強制 headless（launchd 半夜自動跑用）
HEADLESS = os.getenv('TZG_HEADLESS', '0') == '1'

def log(msg):
    print(f'[{datetime.now():%H:%M:%S}] {msg}')

def is_logged_in(page):
    """確認目前頁面是否已登入"""
    url = page.url
    log(f'目前 URL：{url}')
    # 只要不在 SSO 登入頁，且在 shoplineapp.com 後台，就視為已登入
    return 'admin.shoplineapp.com' in url and 'sso.' not in url and '/oauth/' not in url

def manual_login(page):
    """開啟瀏覽器讓使用者手動登入（含 2FA）"""
    log('=' * 50)
    log('需要手動登入 — 請看【彈出的 Chromium 瀏覽器視窗】')
    log('（不是你平常用的 Chrome，是另一個新開的視窗）')
    log('  1. 在那個視窗輸入帳號密碼')
    log('  2. 輸入 Google Authenticator 驗證碼')
    log('  3. 進入後台後腳本會自動繼續（不需要按 Enter）')
    log('=' * 50)

    page.goto(LOGIN_URL, wait_until='load', timeout=30000)

    # ── 步驟 1：填 email ──
    try:
        page.wait_for_selector('input[type="email"]', timeout=8000)
        page.locator('input[type="email"]').first.fill(EMAIL)
        page.wait_for_timeout(500)
        # 點送出（可能是 Next 或直接 Sign In）
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        log('已填 email 並送出')
    except PlaywrightTimeout:
        log('[!] 找不到 email 欄位，請手動操作')

    # ── 步驟 2：填 password（部分 SSO 分兩頁）──
    try:
        page.wait_for_selector('input[type="password"]', timeout=8000)
        page.locator('input[type="password"]').first.fill(PASSWORD)
        page.wait_for_timeout(500)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        log('已填密碼並送出')
    except PlaywrightTimeout:
        log('[!] 找不到密碼欄位，可能已跳過')

    # ── 步驟 3：等使用者輸入 2FA，偵測到 2FA 欄位後自動送出 ──
    log('等待 2FA 驗證碼頁面...')
    try:
        # 常見的 2FA 輸入框選擇器
        page.wait_for_selector(
            'input[name*="otp"], input[name*="code"], input[name*="token"], '
            'input[placeholder*="驗證"], input[placeholder*="code"], '
            'input[autocomplete="one-time-code"]',
            timeout=15000
        )
        log('偵測到 2FA 輸入框，請在 Chromium 視窗輸入驗證碼...')

        # 等使用者輸入完 6 位數字後自動送出
        otp_input = page.locator(
            'input[name*="otp"], input[name*="code"], input[name*="token"], '
            'input[placeholder*="驗證"], input[placeholder*="code"], '
            'input[autocomplete="one-time-code"]'
        ).first

        # 監聽：當輸入框有 6 個字元時自動點送出
        for _ in range(60):  # 最多等 60 秒
            val = otp_input.input_value()
            if val and len(val.replace(' ', '')) >= 6:
                page.wait_for_timeout(300)
                page.locator('button[type="submit"], input[type="submit"]').first.click()
                log('已自動送出 2FA 驗證碼')
                break
            page.wait_for_timeout(1000)
        else:
            log('[!] 未偵測到輸入完成，請手動點送出')

    except PlaywrightTimeout:
        log('[!] 未偵測到 2FA 頁面（可能此帳號不需要 2FA）')

    # ── 最終等待：跳轉到後台（最多 3 分鐘）──
    log('等待進入後台...')
    try:
        page.wait_for_url('**/admin/tzgrotw251/**', timeout=180000)
        log(f'[✓] 登入成功！URL：{page.url}')
        return True
    except PlaywrightTimeout:
        log(f'[X] 等待逾時，目前 URL：{page.url}')
        return False

def parse_date_range():
    """從命令列參數決定要下載的日期範圍（回傳 YYYY/MM/DD 格式）"""
    p = argparse.ArgumentParser(description='Shopline 訂單報表下載')
    p.add_argument('--month', type=str, metavar='YYYY-MM',
                   help='整個月份（例：2026-03）')
    p.add_argument('--start', type=str, metavar='YYYY-MM-DD', help='起始日期')
    p.add_argument('--end',   type=str, metavar='YYYY-MM-DD', help='結束日期')
    args = p.parse_args()

    if args.month:
        try:
            dt = datetime.strptime(args.month, '%Y-%m')
        except ValueError:
            print(f'[X] 月份格式錯誤：{args.month}（應為 YYYY-MM）')
            sys.exit(1)
        last_day = _cal.monthrange(dt.year, dt.month)[1]
        return (datetime(dt.year, dt.month, 1).strftime('%Y/%m/%d'),
                datetime(dt.year, dt.month, last_day).strftime('%Y/%m/%d'))
    if args.start and args.end:
        try:
            s = datetime.strptime(args.start, '%Y-%m-%d')
            e = datetime.strptime(args.end,   '%Y-%m-%d')
        except ValueError:
            print(f'[X] 日期格式錯誤（應為 YYYY-MM-DD）')
            sys.exit(1)
        return s.strftime('%Y/%m/%d'), e.strftime('%Y/%m/%d')

    # 預設：當月 1 號 ~ 今天
    today = datetime.now()
    return (today.replace(day=1).strftime('%Y/%m/%d'),
            today.strftime('%Y/%m/%d'))


def run(month_start=None, month_end=None):
    DATA_DIR.mkdir(exist_ok=True)

    # 若沒傳入日期，預設用本月 1 號 ~ 今天
    today = datetime.now()
    if month_start is None:
        month_start = today.replace(day=1).strftime('%Y/%m/%d')
    if month_end is None:
        month_end = today.strftime('%Y/%m/%d')
    log(f'匯出範圍：{month_start} ~ {month_end}')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=100 if not HEADLESS else 0)

        # ── 載入或建立 Session ────────────────────────────────
        if SESSION_FILE.exists():
            log(f'載入已儲存的 Session：{SESSION_FILE}')
            storage = json.loads(SESSION_FILE.read_text(encoding='utf-8'))
            context = browser.new_context(storage_state=storage, accept_downloads=True)
        else:
            log('沒有 Session，將手動登入')
            context = browser.new_context(accept_downloads=True)

        page = context.new_page()

        # ── 1. 確認登入狀態 ───────────────────────────────────
        log('確認登入狀態...')
        page.goto(REPORT_URL, wait_until='load', timeout=30000)

        # 如果跳到 SSO 頁，代表 Session 過期或不存在
        if 'sso' in page.url or not is_logged_in(page):
            log('Session 已過期或不存在，需要重新登入')
            if not manual_login(page):
                browser.close()
                sys.exit(1)

            # 儲存新 Session
            storage = context.storage_state()
            SESSION_FILE.write_text(json.dumps(storage), encoding='utf-8')
            log(f'[✓] Session 已儲存：{SESSION_FILE}（下次免登入）')

            # 重新前往報表頁
            page.goto(REPORT_URL, wait_until='load', timeout=30000)
        else:
            log('Session 有效，直接進入報表頁')

        # ── 2. 前往報表匯出頁 ────────────────────────────────
        log('前往報表匯出頁...')
        page.goto(REPORT_URL, wait_until='load', timeout=30000)

        # 等待匯出區塊載入
        try:
            page.wait_for_selector('.export-row', timeout=15000)
            log('匯出區塊已載入')
        except PlaywrightTimeout:
            log('[X] 找不到 .export-row，截圖：debug_report.png')
            page.screenshot(path='debug_report.png')
            browser.close()
            sys.exit(1)

        # ── 3. 設定日期範圍 ──────────────────────────────────
        log(f'設定日期：{month_start} ~ {month_end}')

        # Shopline 日期輸入框（報表頁有 start/end date）
        DATE_SEL = 'input[ng-model*="date"], input[placeholder*="yyyy"], input[type="date"]'
        date_inputs = page.locator(DATE_SEL)
        n_dates = date_inputs.count()
        log(f'找到 {n_dates} 個日期輸入框')

        # 先記錄 ng-model 屬性供除錯
        info = page.evaluate(f'''() => {{
            const els = document.querySelectorAll('{DATE_SEL}');
            return Array.from(els).map(el => ({{
                ngModel: el.getAttribute('ng-model'),
                type: el.type,
                placeholder: el.placeholder,
                value: el.value
            }}));
        }}''')
        log(f'日期框詳情：{info}')

        if n_dates >= 2:
            # ── 方法 A：Angular $setViewValue（最正確的 AngularJS 方式）──
            ng_result = page.evaluate(f'''() => {{
                const inputs = document.querySelectorAll('{DATE_SEL}');
                const log = [];
                function setNgInput(el, val) {{
                    try {{
                        const ctrl  = angular.element(el).controller('ngModel');
                        const scope = angular.element(el).scope();
                        if (ctrl && scope) {{
                            scope.$apply(function() {{
                                ctrl.$setViewValue(val);
                                ctrl.$render();
                            }});
                            log.push('ok:' + (el.getAttribute('ng-model') || el.name || '?'));
                            return;
                        }}
                    }} catch(e) {{ log.push('ngErr:' + e.message.slice(0, 50)); }}
                    // fallback：直接設值 + 事件
                    el.value = val;
                    ['input','change','blur'].forEach(t =>
                        el.dispatchEvent(new Event(t, {{bubbles: true}}))
                    );
                    log.push('fallback:' + (el.getAttribute('ng-model') || '?'));
                }}
                if (inputs[0]) setNgInput(inputs[0], '{month_start}');
                if (inputs[1]) setNgInput(inputs[1], '{month_end}');
                return {{
                    log:    log,
                    values: Array.from(inputs).slice(0, 2).map(el => el.value)
                }};
            }}''')
            log(f'Angular 設定結果：{ng_result}')
            page.wait_for_timeout(600)

            # ── 驗證最終值 ──
            final = page.evaluate(f'''() => {{
                const els = document.querySelectorAll('{DATE_SEL}');
                return Array.from(els).slice(0, 2).map(el => el.value);
            }}''')
            log(f'驗證最終日期值：{final}')
            page.wait_for_timeout(400)
        else:
            log('[!] 找不到日期輸入框，使用頁面預設日期範圍')

        JOBS_URL = f'https://admin.shoplineapp.com/admin/{SHOP_ID}/jobs'

        # ── 4. 點擊匯出，同時攔截 API 回應 ──────────────────────
        log('尋找匯出按鈕...')
        export_btn = page.locator('a.export-item').first
        if export_btn.count() == 0:
            log('[X] 找不到匯出按鈕，截圖：debug_no_btn.png')
            page.screenshot(path='debug_no_btn.png')
            browser.close()
            sys.exit(1)

        timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_safe = month_start.replace('/', '')   # 2026/04/01 → 20260401
        end_safe   = month_end.replace('/', '')
        filename   = f'shopline_{start_safe}_to_{end_safe}_{timestamp}.xlsx'
        save_path = DATA_DIR / filename

        # ── 第一次點擊：打開選擇欄位對話框 ──
        log('第一次點擊匯出...')
        export_btn.click()
        page.wait_for_timeout(2000)

        # 截圖確認對話框內容（第一次）
        page.screenshot(path='debug_export_modal.png')
        log('截圖：debug_export_modal.png（對話框）')

        # ── 第二次點擊：對話框底部的藍色「匯出」確認按鈕 ──
        # 對話框結構：標題「匯出訂單報表」，底部有「取消」和藍色「匯出」
        log('等待對話框出現...')
        try:
            # 等對話框標題出現
            page.wait_for_selector(
                'text=匯出訂單報表, text=匯出訂單',
                timeout=8000
            )
            log('對話框已出現')
        except PlaywrightTimeout:
            log('[!] 未偵測到對話框標題，繼續嘗試...')

        page.wait_for_timeout(1000)

        # 對話框底部的藍色確認「匯出」按鈕
        # 截圖顯示按鈕在底部右側，class 應含 btn-primary
        confirm_btn = page.locator(
            'button.btn-primary:has-text("匯出"), '
            'a.btn-primary:has-text("匯出"), '
            'button.btn.btn-primary'
        ).last  # 用 .last 取底部最後一個，避免點到背景的按鈕

        if confirm_btn.count() > 0:
            log('找到對話框確認按鈕，第二次點擊匯出...')
            # 隱藏 Intercom 聊天視窗（它浮在按鈕上方擋住點擊）
            page.evaluate('''() => {
                const ic = document.getElementById('intercom-container');
                if (ic) ic.style.display = 'none';
            }''')
            page.wait_for_timeout(500)
            # 用 JS .click() 觸發 AngularJS ng-click 事件
            page.evaluate('''() => {
                const btn = document.querySelector(
                    'button.btn-primary[ng-click="export()"], '  +
                    'button.btn-primary.ng-binding'
                );
                if (btn) btn.click();
            }''')
            log('已送出第二次點擊（JS click）')
        else:
            log('[!] 找不到藍色確認按鈕，截圖：debug_modal_btn.png')
            page.screenshot(path='debug_modal_btn.png')
            browser.close()
            sys.exit(1)

        log('已送出匯出請求，等待 Shopline 伺服器處理（約 1 分鐘）...')

        # ── 5. 輪詢 /jobs 頁等待下載連結出現 ─────────────────────
        # Shopline 需要約 1 分鐘才能生成檔案，先等 60 秒再開始檢查
        page.wait_for_timeout(60000)
        log('開始輪詢下載連結...')

        def find_download_btn(page):
            """嘗試多種方式找到下載按鈕，回傳 (locator, href) 或 None"""
            # 先用 JS 列出所有按鈕文字（除錯用）
            btn_texts = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button, a'))
                    .map(el => el.textContent.trim())
                    .filter(t => t.length > 0 && t.length < 20);
            }""")
            log(f'[debug] 頁面文字元素：{btn_texts[:30]}')

            # 方法 1：JS 直接找含「下載」的按鈕並取得 href（最可靠）
            result = page.evaluate("""() => {
                const candidates = Array.from(
                    document.querySelectorAll('button, a, [role="button"]')
                );
                for (const el of candidates) {
                    const t = el.textContent.trim();
                    if (t === '下載' || t.includes('下載') || t.includes('Download')) {
                        return {
                            tag:  el.tagName,
                            text: t,
                            href: el.href || el.getAttribute('href') || '',
                            cls:  el.className
                        };
                    }
                }
                // 也找 href 包含 csv/xlsx 的連結
                for (const a of document.querySelectorAll('a[href]')) {
                    const href = a.href || '';
                    if (href.includes('.csv') || href.includes('.xlsx') ||
                        href.includes('download')) {
                        return { tag: 'A', text: a.textContent.trim(),
                                 href: href, cls: a.className };
                    }
                }
                return null;
            }""")

            if result:
                log(f'[JS] 找到下載元素：{result}')
                if result.get('href'):
                    # 有 href → 直接用連結下載
                    return page.locator(f'a[href="{result["href"]}"]').first, result['href']
                else:
                    # 無 href → 用文字定位點擊
                    return page.get_by_text('下載', exact=True).first, ''

            # 方法 2：Playwright role-based locator
            role_btn = page.get_by_role('button', name='下載')
            if role_btn.count() > 0:
                log('[role] 找到下載按鈕')
                return role_btn.first, ''

            # 方法 3：get_by_text（含部分符合）
            txt_btn = page.get_by_text('下載', exact=True)
            if txt_btn.count() > 0:
                log('[text] 找到下載文字元素')
                return txt_btn.first, ''

            return None, None

        # 最多再等 3 分鐘（每 15 秒一次）
        for i in range(12):
            try:
                page.goto(JOBS_URL, wait_until='load', timeout=30000)
                # 等 Angular 渲染完成（等 table 或 job row 出現）
                try:
                    page.wait_for_selector('table tr, .job-row', timeout=8000)
                except PlaywrightTimeout:
                    pass
                page.wait_for_timeout(2000)

                # 截圖供第一次確認（只截一次）
                if i == 0:
                    page.screenshot(path='debug_jobs_page.png', full_page=True)
                    log('截圖：debug_jobs_page.png')

                dl_link, href = find_download_btn(page)

                if dl_link is not None:
                    log(f'[✓] 準備下載，href={href[:80]}')
                    with page.expect_download(timeout=30000) as dl_info:
                        dl_link.click()
                    download = dl_info.value
                    download.save_as(save_path)
                    log(f'[✓] 下載完成：{save_path}')
                    browser.close()
                    return str(save_path)

                elapsed = 60 + (i + 1) * 15
                log(f'[{i+1}/12] 尚未就緒，繼續等待... (共 {elapsed} 秒)')
                page.wait_for_timeout(12000)

            except Exception as e:
                log(f'[!] 輪詢時出錯：{e}，繼續重試...')
                page.wait_for_timeout(15000)

        log('[X] 等待超時（4分鐘），截圖：debug_jobs_timeout.png')
        page.screenshot(path='debug_jobs_timeout.png', full_page=True)
        browser.close()
        sys.exit(1)

# ─────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print(' Shopline 自動下載 v3.1')
    print('=' * 60)
    start, end = parse_date_range()
    try:
        path = run(start, end)
        print(f'\n[✅ 成功] 檔案已存至：{path}')
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f'\n[❌ 失敗] {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
