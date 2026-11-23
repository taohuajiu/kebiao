#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点金课表 · 全员数据生成器
=========================
从金山文档（或本地已下载的 xlsx）里**把每位老师的课都抽出来**，
生成前端网页要用的数据文件：

    data/all_teachers.json   标准 JSON（给云端 / 接口 / 其他程序用）
    data/all_teachers.js     window.SCHEDULE_DATA = {...}（网页双击就能用，不用起服务）

只抽「日期 / 时间段 / 课程名」，不算课酬、不导出 Excel —— 工资那套仍由
workbubby/课表工具/课表提取.py 负责，两者互不影响。

用法
----
    python 生成全员课表.py                     # 用本机已缓存的课表
    python 生成全员课表.py --refresh           # 先从金山文档拉最新表（需要 cookie.txt）
    python 生成全员课表.py --file D:/某处/课表.xlsx
    python 生成全员课表.py --out-dir ./data

依赖：pip install openpyxl
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("缺少依赖 openpyxl，请先执行： pip install openpyxl")

# ============================== 配置区 ==============================
KDOCS_URL = "https://www.kdocs.cn/l/co6ZLHXYhHuL"
KDOCS_FILE_ID = "mz1ofYQ1q1MXuz9B8oMz1xsgDoo8HT5vY"

BASE_DIR = Path(__file__).resolve().parent
# 一律按北京时间算"今天/现在"。GitHub Actions 的机器是 UTC，
# 直接 datetime.now() 会差 8 小时（早上 06:30 那次甚至会算成前一天）。
CN_TZ = dt.timezone(dt.timedelta(hours=8))
# 沿用「课表工具」里已经下好的源表和 cookie，避免重复配置
TOOL_DIR = BASE_DIR.parent / "workbubby" / "课表工具"
SOURCE_DEFAULT = TOOL_DIR / "课表源文件" / "26年度上学期课表.xlsx"
COOKIE_DEFAULT = TOOL_DIR / "cookie.txt"
OUT_DIR_DEFAULT = BASE_DIR / "data"

NAME_HEADER_HINTS = ("姓名", "老师", "教师", "任课", "授课")
DATE_HEADER_HINTS = ("日期", "上课日期")
TIME_HEADER_PATTERN = re.compile(r"\d{1,2}\s*[:：]\s*\d{2}")
SPLIT_PATTERN = re.compile(r"[、,，/;；\n]+")
WEEKDAY_CN = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
# ===================================================================

if hasattr(sys.stdout, "reconfigure"):        # Windows 控制台中文不乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ------------------------------ 小工具 ------------------------------
def clean_text(value):
    """去掉换行、<br/>、所有空白。"""
    if value is None:
        return ""
    if isinstance(value, str):
        s = value.replace("\r", " ").replace("\n", " ")
        s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
        return re.sub(r"[\s\u3000\u00a0]+", "", s)
    return str(value).strip()


def to_date(value, today):
    """单元格 → date；认 2026年11月17日 / 11月17号 / 2026-11-17 等写法。"""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)) and 20000 < value < 80000:
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(value))

    s = clean_text(value)
    if not s:
        return None

    def build(y, m, d):
        try:
            return dt.date(y, m, d)
        except ValueError:
            return None

    m = re.search(r"(\d{2,4})\s*[年/\-.]\s*(\d{1,2})\s*[月/\-.]\s*(\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return build(y, mo, d)

    m = re.search(r"(\d{1,2})\s*[月/\-.]\s*(\d{1,2})", s)
    if m:
        mo, d = int(m.group(1)), int(m.group(2))
        cands = [build(y, mo, d) for y in (today.year - 1, today.year, today.year + 1)]
        cands = [c for c in cands if c]
        if cands:
            return min(cands, key=lambda c: abs((c - today).days))   # 表里不带年份，取离今天最近的
    return None


def cn_now():
    """当前北京时间（不受机器时区影响）。"""
    return dt.datetime.now(CN_TZ)


def time_start(header):
    """'13:30-15:30' → 810（分钟），用来给当天的课排序。"""
    m = re.search(r"(\d{1,2})\s*[:：]\s*(\d{2})", header or "")
    if not m:
        return 9999
    return int(m.group(1)) * 60 + int(m.group(2))


# ---------------------------- 取数据源 ----------------------------
def download_from_kdocs(cookie, dest):
    api = ("https://www.kdocs.cn/api/v3/office/file/{}/download"
           "?isblocks=false&support_checksums=1").format(KDOCS_FILE_ID)
    headers = {
        "Cookie": cookie,
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36"),
        "Referer": KDOCS_URL,
        "Accept": "*/*",
    }

    def fetch(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read()

    try:
        data = fetch(api)
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "ignore")
        raise RuntimeError("下载失败 HTTP {}：{}（cookie 可能过期了）".format(e.code, body))

    if not data[:2] == b"PK":                       # 有时返回 JSON 里再套一个直链
        try:
            info = json.loads(data.decode("utf-8", "ignore"))
        except Exception:
            info = {}
        inner = info.get("url") or (info.get("data") or {}).get("url")
        if not inner:
            raise RuntimeError("接口没有返回文件流：" + data[:200].decode("utf-8", "ignore"))
        data = fetch(inner)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print("已从金山文档下载：{}（{} KB）".format(dest.name, len(data) // 1024))
    return dest


def read_cookie():
    """优先读环境变量 WPS_COOKIE（GitHub Actions 用），其次读本地 cookie.txt。"""
    env = (os.environ.get("WPS_COOKIE") or "").strip()
    if env:
        return re.sub(r"^cookie\s*:\s*", "", env, flags=re.I).strip()
    if COOKIE_DEFAULT.exists():
        s = COOKIE_DEFAULT.read_text(encoding="utf-8").strip()
        return re.sub(r"^cookie\s*:\s*", "", s, flags=re.I).strip()
    return ""


def get_source(explicit, refresh):
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            sys.exit("找不到文件：{}".format(p))
        print("数据源：{}".format(p))
        return p

    cookie = read_cookie()
    if refresh and cookie:
        print("数据源：金山文档（--refresh）")
        try:
            return download_from_kdocs(cookie, SOURCE_DEFAULT)
        except Exception as e:
            print("！自动下载失败：{}".format(e))
            if not SOURCE_DEFAULT.exists():
                sys.exit("下载失败，本地也没有缓存表，请手动放一份到 {}".format(SOURCE_DEFAULT))
            print("  改用本地缓存的表继续")

    if SOURCE_DEFAULT.exists():
        print("数据源：本地缓存 {}".format(SOURCE_DEFAULT.name))
        return SOURCE_DEFAULT

    if cookie:
        print("数据源：金山文档")
        return download_from_kdocs(cookie, SOURCE_DEFAULT)

    sys.exit("找不到课表：请把 xlsx 放到 {}，或用 --file 指定，或配好 cookie.txt 后加 --refresh。"
             .format(SOURCE_DEFAULT))


# ---------------------------- 解析课表 ----------------------------
def locate_header(ws, max_scan=5):
    """返回 (表头行, 姓名列, 日期列)。"""
    name_col = date_col = None
    header_row = 1
    for r in range(1, min(max_scan, ws.max_row or 1) + 1):
        for c in range(1, (ws.max_column or 1) + 1):
            txt = clean_text(ws.cell(row=r, column=c).value)
            if not txt or len(txt) > 6:
                continue
            if name_col is None and any(h in txt for h in NAME_HEADER_HINTS):
                name_col, header_row = c, r
            if date_col is None and any(h in txt for h in DATE_HEADER_HINTS):
                date_col = c
        if name_col:
            break
    if name_col is None:
        name_col, header_row = 1, 1
    if date_col is None:
        date_col = name_col + 1
    return header_row, name_col, date_col


def collect_all(wb, today):
    """把每张表里每位老师的课收集起来。

    返回 teachers: {姓名: {"sheet": 表名, "days": {date: [(排序键, 时间段, 课程名)]}}}
    """
    teachers = {}
    for ws in wb.worksheets:
        header_row, name_col, date_col = locate_header(ws)
        time_cols = []
        for c in range(1, (ws.max_column or 1) + 1):
            h = clean_text(ws.cell(row=header_row, column=c).value)
            if TIME_HEADER_PATTERN.search(h):
                time_cols.append((c, h))
        if not time_cols:
            continue

        current = ""
        for r in range(header_row + 1, (ws.max_row or 0) + 1):
            filled = clean_text(ws.cell(row=r, column=name_col).value)
            if filled:
                current = filled          # 合并单元格只有首行有值，往下沿用
            if not current:
                continue
            d = to_date(ws.cell(row=r, column=date_col).value, today)
            if d is None:
                continue

            for c, h in time_cols:
                raw = clean_text(ws.cell(row=r, column=c).value)
                if not raw:
                    continue
                for part in SPLIT_PATTERN.split(raw):
                    part = part.strip()
                    if not part:
                        continue
                    item = teachers.setdefault(
                        current, {"sheet": ws.title, "days": {}})
                    item["days"].setdefault(d, []).append((time_start(h), h, part))
    return teachers


def build_payload(teachers, today):
    payload = {"teachers": {}}
    lesson_count = 0
    for name, info in teachers.items():
        days = []
        for d in sorted(info["days"]):
            classes = [{"time": h, "course": course}
                       for _, h, course in sorted(info["days"][d], key=lambda x: x[0])]
            lesson_count += len(classes)
            days.append({
                "date": d.isoformat(),
                "dateLabel": "{}月{}日".format(d.month, d.day),
                "weekday": WEEKDAY_CN[d.weekday()],
                "classes": classes,
            })
        payload["teachers"][name] = {"sheet": info["sheet"], "days": days}

    payload.update({
        "generatedAt": cn_now().strftime("%Y-%m-%d %H:%M"),
        "generatedDate": today.isoformat(),
        "source": "金山文档 · 26年度上学期课表",
        "teacherCount": len(payload["teachers"]),
        "lessonCount": lesson_count,
    })
    return payload


# ------------------------------ 主流程 ------------------------------
def main():
    ap = argparse.ArgumentParser(description="点金课表 · 全员数据生成器")
    ap.add_argument("--file", default=None, help="指定本地课表 xlsx")
    ap.add_argument("--refresh", action="store_true", help="先从金山文档拉最新表")
    ap.add_argument("--out-dir", default=None, help="输出目录，默认 ./data")
    args = ap.parse_args()

    today = cn_now().date()
    src = get_source(args.file, args.refresh)
    wb = openpyxl.load_workbook(src, data_only=True)

    teachers = collect_all(wb, today)
    if not teachers:
        sys.exit("没有解析到任何老师的课，检查一下源表结构是否变了。")

    payload = build_payload(teachers, today)

    out_dir = Path(args.out_dir) if args.out_dir else OUT_DIR_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "all_teachers.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    js_path = out_dir / "all_teachers.js"
    js_path.write_text(
        "/* 由 生成全员课表.py 自动生成，请勿手改 */\n"
        "window.SCHEDULE_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8")

    # 极小的版本文件：网页每隔几分钟只拉它（几十字节），用于判断要不要重新加载课表
    ver_path = out_dir / "version.json"
    ver_path.write_text(
        json.dumps({
            "generatedAt": payload["generatedAt"],
            "generatedDate": payload["generatedDate"],
            "teacherCount": payload["teacherCount"],
            "lessonCount": payload["lessonCount"],
        }, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    print("\n解析完成：{} 位老师，{} 节课".format(payload["teacherCount"], payload["lessonCount"]))
    for name, info in payload["teachers"].items():
        n = sum(len(x["classes"]) for x in info["days"])
        print("  {:<8} {:<6} {:>3} 节  {:>2} 天".format(name, info["sheet"], n, len(info["days"])))
    print("\n已生成：")
    print("  {}".format(json_path))
    print("  {}".format(js_path))
    print("  {}  （网页用它检查有没有更新）".format(ver_path))
    print("双击 index.html 即可查看；手机上看效果可用 python -m http.server 起个本地服务。")


if __name__ == "__main__":
    main()
