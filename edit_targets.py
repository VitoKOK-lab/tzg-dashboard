#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 業績目標 / UTM 責任額 編輯工具  v1.0
==============================================================
請執行 edit_targets.bat（雙擊）或：
  python edit_targets.py

修改後會自動儲存到 annual_plan.json。
功能：
  1. 編輯月度業績目標
  2. 管理責任額名單（蝦皮 / LINE OA / 行銷企劃）
  3. 編輯各月責任額配額金額
  4. 顯示當前所有設定
  5. 重新產出月會頁面 + push GitHub
==============================================================
"""
import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

PLAN_FILE = Path(__file__).parent / 'annual_plan.json'

DEFAULT_PLAN = {
    "_說明": "TZG 業績目標。請執行 edit_targets.bat 編輯，不要直接改此 JSON。",
    "_default_monthly": 4500000,
    "monthly": {f"2026-{m:02d}": 4500000 for m in range(1, 13)},
    "quota_holders": [],
    "quotas": {}
}

KNOWN_SOURCES = [
    '直接/官網', 'LINE 來源', 'Facebook 來源', 'Instagram 來源',
    '業務推薦', 'TikTok 來源', 'Threads 來源', 'YouTube 來源',
    '內容導流', '蝦皮', '直播', '實體店', 'WhatsApp', '其他'
]


def fmt_n(v):
    return f"{int(v):,}"


def fmt_money(v):
    """將數字格式化為 NT$ 金額字串"""
    return f"NT$ {fmt_n(v):>12}"


def parse_money(s):
    """把使用者輸入的金額字串轉為 int（支援 4500000、4,500,000、450萬）"""
    s = s.strip().replace(',', '').replace(' ', '')
    if not s:
        return None
    if '萬' in s:
        try:
            return int(float(s.replace('萬', '')) * 10000)
        except ValueError:
            return None
    try:
        return int(float(s))
    except ValueError:
        return None


def migrate_old_format(data):
    """把舊的扁平格式（YYYY-MM 直接在 root）轉成新格式"""
    if 'monthly' in data:
        return data  # 已經是新格式

    new_data = {
        "_說明":            data.get('_說明', DEFAULT_PLAN['_說明']),
        "_default_monthly": int(data.get('_default', data.get('_default_monthly', 4500000))),
        "monthly":          {},
        "quota_holders":    data.get('quota_holders', []),
        "quotas":           data.get('quotas', {}),
    }
    for k, v in data.items():
        if k.startswith('_'):
            continue
        if len(k) == 7 and k[4] == '-':
            try:
                new_data['monthly'][k] = int(v)
            except (TypeError, ValueError):
                pass
    return new_data


def load_plan():
    if not PLAN_FILE.exists():
        return DEFAULT_PLAN.copy()
    try:
        data = json.loads(PLAN_FILE.read_text(encoding='utf-8'))
        return migrate_old_format(data)
    except Exception as e:
        print(f"  [!] 讀取 annual_plan.json 失敗：{e}")
        return DEFAULT_PLAN.copy()


def save_plan(data):
    PLAN_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8'
    )


def hr():
    print("─" * 60)


def header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────
# 1. 月度業績目標
# ─────────────────────────────────────────────────────────────
def edit_monthly_targets(plan):
    while True:
        header("月度業績目標")
        items = sorted(plan['monthly'].items())
        for k, v in items:
            print(f"    {k}    {fmt_money(v)}")
        print()
        print("  指令：")
        print("    輸入 YYYY-MM         → 編輯該月")
        print("    all                  → 把所有月份設成同一個值")
        print("    add YYYY-MM 金額     → 新增月份（或覆蓋）")
        print("    q                    → 返回主選單")
        cmd = input("\n  > ").strip()

        if cmd.lower() == 'q':
            return

        if cmd.lower() == 'all':
            v = input("  全部月份統一目標：")
            num = parse_money(v)
            if num is None:
                print("  [X] 數字錯誤")
                continue
            for k in plan['monthly']:
                plan['monthly'][k] = num
            save_plan(plan)
            print(f"  ✓ 已將全部月份設為 NT$ {fmt_n(num)}")
            continue

        if cmd.lower().startswith('add '):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                print("  [X] 用法：add YYYY-MM 金額")
                continue
            ym, val = parts[1], parts[2]
            if not (len(ym) == 7 and ym[4] == '-'):
                print("  [X] 月份格式錯誤")
                continue
            num = parse_money(val)
            if num is None:
                print("  [X] 金額錯誤")
                continue
            plan['monthly'][ym] = num
            save_plan(plan)
            print(f"  ✓ {ym} = NT$ {fmt_n(num)}")
            continue

        # 編輯單一月份
        if len(cmd) == 7 and cmd[4] == '-':
            if cmd not in plan['monthly']:
                print(f"  [!] {cmd} 不存在，將自動新增")
            cur = plan['monthly'].get(cmd, plan.get('_default_monthly', 4500000))
            print(f"\n  目前 {cmd} = NT$ {fmt_n(cur)}")
            v = input("  新值（按 Enter 不變）：").strip()
            if not v:
                continue
            num = parse_money(v)
            if num is None:
                print("  [X] 數字錯誤")
                continue
            plan['monthly'][cmd] = num
            save_plan(plan)
            print(f"  ✓ 已更新 {cmd} = NT$ {fmt_n(num)}")
            continue

        print("  [X] 無法辨識的指令")


# ─────────────────────────────────────────────────────────────
# 2. 責任額名單
# ─────────────────────────────────────────────────────────────
def manage_quota_holders(plan):
    while True:
        header("UTM 責任額名單")
        holders = plan.get('quota_holders', [])
        if not holders:
            print("  (尚未新增任何責任額)")
        else:
            for i, h in enumerate(holders, 1):
                t = h.get('match_type', '?')
                v = h.get('match_value', '')
                print(f"    {i}. {h['name']:18s}   [{t}: {v}]")
                if h.get('note'):
                    print(f"       備註：{h['note']}")
        print()
        print("  a       → 新增責任額")
        if holders:
            print("  e <編號> → 編輯責任額")
            print("  d <編號> → 刪除責任額")
        print("  q        → 返回")
        cmd = input("\n  > ").strip().lower()

        if cmd == 'q':
            return
        if cmd == 'a':
            add_quota_holder(plan)
        elif cmd.startswith('e ') and holders:
            try:
                idx = int(cmd.split()[1]) - 1
                if 0 <= idx < len(holders):
                    edit_quota_holder(plan, idx)
            except (ValueError, IndexError):
                print("  [X] 編號錯誤")
        elif cmd.startswith('d ') and holders:
            try:
                idx = int(cmd.split()[1]) - 1
                if 0 <= idx < len(holders):
                    delete_quota_holder(plan, idx)
            except (ValueError, IndexError):
                print("  [X] 編號錯誤")
        else:
            print("  [X] 無法辨識")


def add_quota_holder(plan):
    print("\n  新增責任額")
    name = input("  名稱（例：春季企劃A、LINE OA、蝦皮）：").strip()
    if not name:
        print("  [X] 取消")
        return

    print("\n  匹配方式：")
    print("    1. keyword（在訂單『推薦活動』欄位裡找關鍵字，例：#企劃A、lineoa）")
    print("    2. source （訂單來源分類完全匹配）")
    mt = input("  選擇 [1/2]：").strip()
    if mt == '1':
        match_type = 'keyword'
        match_value = input("  關鍵字（不分大小寫，例：#企劃A）：").strip()
    elif mt == '2':
        match_type = 'source'
        print("  常見來源值：")
        for s in KNOWN_SOURCES:
            print(f"    - {s}")
        match_value = input("  來源名稱（必須完全相符）：").strip()
    else:
        print("  [X] 取消")
        return

    if not match_value:
        print("  [X] 取消")
        return

    note = input("  備註（可空）：").strip()

    # 自動產生 id
    base_id = ''.join(c for c in name.lower() if c.isalnum() or c == '_')
    if not base_id:
        base_id = f'q{len(plan.get("quota_holders", [])) + 1}'
    holder_id = base_id[:20]
    existing_ids = {h['id'] for h in plan.get('quota_holders', [])}
    i = 1
    while holder_id in existing_ids:
        holder_id = f"{base_id[:18]}_{i}"
        i += 1

    holder = {
        "id":          holder_id,
        "name":        name,
        "match_type":  match_type,
        "match_value": match_value,
    }
    if note:
        holder['note'] = note

    plan.setdefault('quota_holders', []).append(holder)
    save_plan(plan)
    print(f"  ✓ 已新增「{name}」（id={holder_id}）")


def edit_quota_holder(plan, idx):
    h = plan['quota_holders'][idx]
    print(f"\n  編輯：{h['name']}  [{h.get('match_type')}: {h.get('match_value')}]")
    new_name = input(f"  新名稱（Enter 不變）：").strip()
    new_value = input(f"  新匹配值（Enter 不變）：").strip()
    new_note = input(f"  新備註（Enter 不變、輸入 - 移除）：").strip()
    if new_name:
        h['name'] = new_name
    if new_value:
        h['match_value'] = new_value
    if new_note == '-':
        h.pop('note', None)
    elif new_note:
        h['note'] = new_note
    save_plan(plan)
    print("  ✓ 已更新")


def delete_quota_holder(plan, idx):
    h = plan['quota_holders'][idx]
    confirm = input(f"  確定刪除「{h['name']}」？(y/N)：").strip().lower()
    if confirm != 'y':
        return
    plan['quota_holders'].pop(idx)
    # 連帶清掉所有月份的配額
    for ym in list(plan.get('quotas', {}).keys()):
        plan['quotas'][ym].pop(h['id'], None)
        if not plan['quotas'][ym]:
            del plan['quotas'][ym]
    save_plan(plan)
    print(f"  ✓ 已刪除「{h['name']}」")


# ─────────────────────────────────────────────────────────────
# 3. 各月責任額配額
# ─────────────────────────────────────────────────────────────
def edit_quotas(plan):
    holders = plan.get('quota_holders', [])
    if not holders:
        print("\n  [!] 請先新增責任額名單（主選單選項 2）")
        return

    while True:
        header("各月責任額配額")
        # 顯示當前有設定的月份
        quotas = plan.get('quotas', {})
        if quotas:
            print("  已設定的月份：")
            for ym in sorted(quotas.keys()):
                vals = quotas[ym]
                summary = ' / '.join(
                    f"{h['name']}={fmt_n(vals.get(h['id'], 0))}" for h in holders
                )
                print(f"    {ym}：{summary}")
        else:
            print("  (尚未設定任何月份配額)")
        print()
        ym = input("  輸入要編輯的月份 YYYY-MM（或 q 返回）：").strip()
        if ym.lower() == 'q':
            return
        if not (len(ym) == 7 and ym[4] == '-'):
            print("  [X] 格式錯誤")
            continue

        qmap = plan.setdefault('quotas', {}).setdefault(ym, {})
        print(f"\n  ── 編輯 {ym} 的責任額配額 ──")
        for i, h in enumerate(holders, 1):
            cur = qmap.get(h['id'], 0)
            v = input(f"    {i}. {h['name']:18s}（目前 {fmt_n(cur)}，Enter 不變）：").strip()
            if v:
                num = parse_money(v)
                if num is not None:
                    qmap[h['id']] = num

        # 清掉空的
        if not qmap:
            del plan['quotas'][ym]
        save_plan(plan)
        print(f"\n  ✓ {ym} 已更新")


# ─────────────────────────────────────────────────────────────
# 4. 顯示當前所有設定
# ─────────────────────────────────────────────────────────────
def show_all(plan):
    header("當前所有設定")

    print("\n[ 月度業績目標 ]")
    for ym, t in sorted(plan.get('monthly', {}).items()):
        print(f"    {ym}    {fmt_money(t)}")
    if '_default_monthly' in plan:
        print(f"    （預設值：{fmt_money(plan['_default_monthly'])}）")

    holders = plan.get('quota_holders', [])
    print(f"\n[ 責任額名單 ]  共 {len(holders)} 個")
    if holders:
        for i, h in enumerate(holders, 1):
            print(f"    {i}. {h['name']:18s}   [{h['match_type']}: {h['match_value']}]")
            if h.get('note'):
                print(f"       備註：{h['note']}")

    quotas = plan.get('quotas', {})
    if holders and quotas:
        print(f"\n[ 各月責任額配額 ]")
        for ym in sorted(quotas.keys()):
            print(f"    {ym}:")
            for h in holders:
                v = quotas[ym].get(h['id'], 0)
                tag = '' if v > 0 else '  ← 未設定'
                print(f"      {h['name']:18s} {fmt_money(v)}{tag}")

    print()
    input("  按 Enter 返回主選單...")


# ─────────────────────────────────────────────────────────────
# 5. 重新產出 + push
# ─────────────────────────────────────────────────────────────
def regenerate_and_push():
    header("重新產出月會頁面")
    print("\n  [1/3] 執行 generate_monthly_review.py ...\n")
    here = Path(__file__).parent
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    r1 = subprocess.run([sys.executable, 'generate_monthly_review.py'],
                        cwd=str(here), env=env)
    if r1.returncode != 0:
        print("\n  [X] 月會頁面產生失敗")
        return
    print("\n  [✓] 月會頁面已更新")

    print("\n  [2/3] 是否同時更新日報 dashboard？(y/N)")
    ans = input("  > ").strip().lower()
    if ans == 'y':
        r2 = subprocess.run([sys.executable, 'generate_daily.py'],
                            cwd=str(here), env=env)
        if r2.returncode != 0:
            print("\n  [!] 日報產生失敗（不影響後續流程）")
        else:
            print("\n  [✓] 日報已更新")

    print("\n  [3/3] 推送到 GitHub？(y/N)")
    ans = input("  > ").strip().lower()
    if ans == 'y':
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        subprocess.run(['git', 'add', 'annual_plan.json',
                        'output/monthly_review.html',
                        'output/dashboard_latest.html'],
                       cwd=str(here))
        subprocess.run(['git', 'commit', '-m', f'Update targets {ts}'],
                       cwd=str(here))
        r = subprocess.run(['git', 'push', 'origin', 'main'], cwd=str(here))
        if r.returncode == 0:
            print("\n  [✓] 已 push 到 GitHub。約 1–2 分鐘後 GitHub Pages 更新。")
        else:
            print("\n  [!] push 失敗。請手動執行 git push origin main")


# ─────────────────────────────────────────────────────────────
# 主選單
# ─────────────────────────────────────────────────────────────
def main_menu():
    while True:
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + "  TZG 業績目標 / UTM 責任額 管理工具".ljust(56) + "  ║")
        print("╠" + "═" * 58 + "╣")
        print("║  1. 編輯月度業績目標".ljust(59) + "║")
        print("║  2. 管理責任額名單（行銷企劃 / LINE OA / 蝦皮）".ljust(54) + "║")
        print("║  3. 編輯各月責任額配額".ljust(58) + "║")
        print("║  4. 顯示當前所有設定".ljust(59) + "║")
        print("║  5. 重新產出月會頁面 + push GitHub".ljust(57) + "║")
        print("║  0. 結束".ljust(60) + "║")
        print("╚" + "═" * 58 + "╝")
        choice = input("\n  選擇： ").strip()

        plan = load_plan()

        if choice == '1':
            edit_monthly_targets(plan)
        elif choice == '2':
            manage_quota_holders(plan)
        elif choice == '3':
            edit_quotas(plan)
        elif choice == '4':
            show_all(plan)
        elif choice == '5':
            regenerate_and_push()
        elif choice == '0':
            print("\n  Bye! 別忘了下次有改完目標要 push 到 GitHub 才會全機構生效。")
            print()
            return
        else:
            print("  [X] 無效選擇")


if __name__ == '__main__':
    try:
        # Windows 設成 UTF-8
        if sys.platform == 'win32':
            os.system('chcp 65001 > nul')

        # 第一次跑會自動把舊格式遷移到新格式
        plan = load_plan()
        save_plan(plan)

        main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  [取消]\n")
