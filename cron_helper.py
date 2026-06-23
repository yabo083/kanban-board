#!/usr/bin/env python3
"""Cron helper: read tasks.json and return stats text.

Usage:
    python cron_helper.py summary   # 默认，简要统计
    python cron_helper.py progress  # 午间进度检查
    python cron_helper.py evening   # 晚间日结
    python cron_helper.py weekly    # 周总结
    python cron_helper.py archive   # 自动归档已完成任务
"""
import json, sys, os, urllib.request
from datetime import datetime, timezone, timedelta

DATA_FILE = os.environ.get("KANBAN_DATA_FILE", os.path.join(os.path.dirname(__file__), "data", "tasks.json"))
TZ = timezone(timedelta(hours=8))

def main():
    if not os.path.exists(DATA_FILE):
        print("看板上没有任何任务。")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    today = datetime.now(TZ).strftime("%Y-%m-%d")
    # Only count non-archived for main stats
    active_tasks = [t for t in tasks if not t.get("archived", False)]
    total = len(active_tasks)
    by_status = {"todo": [], "doing": [], "done": []}
    today_done = []

    for t in active_tasks:
        s = t.get("status", "todo")
        if s in by_status:
            by_status[s].append(t)
        if (t.get("completed_at") or "").startswith(today):
            today_done.append(t)

    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if mode == "progress":
        # Mid-day progress check
        active = by_status["doing"] + by_status["todo"]
        if not active:
            print("今天没有待办任务，老师真轻松呢。")
            return
        lines = ["📋 当前任务进度：\n"]
        if by_status["doing"]:
            lines.append("▶ 进行中：")
            for t in by_status["doing"]:
                lines.append(f"  • {t['title']}")
        if by_status["todo"]:
            lines.append("\n⬜ 待办：")
            for t in by_status["todo"]:
                lines.append(f"  • {t['title']}")
        lines.append(f"\n老师，请汇报一下进展吧。")
        print("\n".join(lines))

    elif mode == "evening":
        # Evening summary
        lines = [f"🌙 {today} 日结：\n"]
        if today_done:
            lines.append(f"✅ 今日完成 {len(today_done)} 项：")
            for t in today_done:
                lines.append(f"  • {t['title']}")
        if by_status["doing"]:
            lines.append(f"\n🔄 仍在进行：")
            for t in by_status["doing"]:
                lines.append(f"  • {t['title']}")
        if by_status["todo"]:
            lines.append(f"\n⬜ 未开始：")
            for t in by_status["todo"]:
                lines.append(f"  • {t['title']}")
        archived_count = len([t for t in tasks if t.get("archived", False)])
        lines.append(f"\n总计 {total} 项任务，完成率 {round(len(by_status['done'])/total*100) if total else 0}%。归档 {archived_count} 项。")
        lines.append("老师今天辛苦了，早点休息哦。")
        print("\n".join(lines))

    elif mode == "weekly":
        # Weekly summary
        week_ago = (datetime.now(TZ) - timedelta(days=7)).strftime("%Y-%m-%d")
        week_done = [t for t in active_tasks if (t.get("completed_at") or "") >= week_ago]
        week_added = [t for t in active_tasks if (t.get("created_at") or "") >= week_ago]
        lines = [f"📊 周绩效总结（{week_ago} ~ {today}）：\n"]
        lines.append(f"• 本周新增任务：{len(week_added)}")
        lines.append(f"• 本周完成任务：{len(week_done)}")
        lines.append(f"• 当前总任务数：{total}")
        lines.append(f"• 总完成率：{round(len(by_status['done'])/total*100) if total else 0}%")
        if week_done:
            lines.append("\n本周完成的任务：")
            for t in week_done:
                lines.append(f"  ✅ {t['title']}")
        remaining = by_status["doing"] + by_status["todo"]
        if remaining:
            lines.append("\n下周待处理：")
            for t in remaining:
                lines.append(f"  ⬜ {t['title']}")
        lines.append("\n老师，请继续保持节奏！爱丽丝会支持老师的。")
        print("\n".join(lines))

    elif mode == "archive":
        # Auto-archive completed (done) tasks
        done_tasks = [t for t in tasks if t.get("status") == "done" and not t.get("archived", False)]
        if not done_tasks:
            print("没有需要归档的已完成任务。")
            return
        # Call the batch archive API
        port = os.environ.get("KANBAN_PORT", "8888")
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/archive/batch",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=b"{}"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                count = result.get("archived", 0)
                print(f"📦 已自动归档 {count} 项已完成任务。")
                for t in done_tasks[:count]:
                    print(f"  • {t['title']}")
        except Exception as e:
            # Fallback: directly modify the file
            count = 0
            for t in tasks:
                if t.get("status") == "done" and not t.get("archived", False):
                    t["archived"] = True
                    t["updated_at"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
                    count += 1
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            print(f"📦 已自动归档 {count} 项已完成任务（直接写入）。")
            for t in done_tasks:
                print(f"  • {t['title']}")

if __name__ == "__main__":
    main()
