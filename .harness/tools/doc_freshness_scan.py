# -*- coding: utf-8 -*-
"""文档新鲜度扫描器 — .harness 治理文档的健康度检查。

扫描 .harness/**/*.md，依据 rules/文档元数据规范.md 检查 frontmatter 与新鲜度。
豁免规则（§2）：
  - .harness/index/** 脚本生成物（AST_INDEX.md / COMPLIANCE_REPORT.md / DOC_HEALTH.md 等）
  - .harness/requests/** 需求分析报告（沿用 doc-analysis frontmatter）
  - .harness/changes/shipped/** 历史快照（archived）
  - .harness/changes/active/** 用 created 字段当 last_updated

检查规则：
  a) 非豁免文档缺 frontmatter 或缺必备字段 -> ALERT
  b) status=active 且 last_updated 超过 90 天 -> STALE
  c) 正文反引号引用的、仓库中真实存在的代码路径，其 mtime 晚于 last_updated -> DRIFT-STALE
  d) status=deprecated 但仍被其他 active 文档的 markdown 链接引用 -> ALERT

输出 .harness/index/DOC_HEALTH.md（自身豁免 frontmatter）。
重写全文件时保留 <!-- SECTION:LINK_CHECK --> / <!-- SECTION:DRIFT -->
标记行及标记之后到文件尾的内容不动（若存在）。
退出码：始终 0（报告型）。
"""
import datetime
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".harness"
OUT = HARNESS / "index" / "DOC_HEALTH.md"

STALE_DAYS = 90
REQUIRED_FIELDS = ("title", "status", "last_updated", "owner", "summary")
CHANGE_REQUIRED_FIELDS = ("status", "owner")  # changes/active 模板字段不同

SECTION_MARKERS = ("<!-- SECTION:LINK_CHECK -->", "<!-- SECTION:DRIFT -->")
BACKTICK_PATH = re.compile(r"`([^`\n]+)`")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")


def parse_frontmatter(text):
    """返回 (fields dict, body str)。无 frontmatter 时 fields 为 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    fields = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    if end is None:
        return None, text
    return fields, "\n".join(lines[end + 1:])


def parse_date(s):
    if not s:
        return None
    m = re.search(r"\d{4}-\d{2}-\d{2}", s)
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(0))
    except ValueError:
        return None


def exemption(rel):
    """返回豁免原因或 None。rel 为相对 .harness 的 posix 路径。"""
    if rel.startswith("index/"):
        return "生成物（index/ 脚本产物）"
    if rel.startswith("requests/"):
        return "需求分析报告（requests/）"
    if rel.startswith("changes/shipped/"):
        return "历史快照（changes/shipped，archived）"
    return None


def main():
    docs = sorted(HARNESS.rglob("*.md"))
    today = datetime.date.today()

    scanned = []  # dict(rel, path, fields, body, effective_updated, is_change_active)
    exempted = []
    for p in docs:
        rel = p.relative_to(HARNESS).as_posix()
        reason = exemption(rel)
        if reason:
            exempted.append((rel, reason))
            continue
        text = p.read_text(encoding="utf-8")
        fields, body = parse_frontmatter(text)
        scanned.append({
            "rel": rel, "path": p, "fields": fields, "body": body,
            "is_change_active": rel.startswith("changes/active/"),
        })

    alerts = []      # (level, rel, detail)
    for d in scanned:
        rel = d["rel"]
        fields = d["fields"]
        # 规则 a
        if fields is None:
            alerts.append(("ALERT", rel, "缺少 frontmatter（元数据规范 §1）"))
            d["effective_updated"] = None
            continue
        required = CHANGE_REQUIRED_FIELDS if d["is_change_active"] else REQUIRED_FIELDS
        missing = [k for k in required if not fields.get(k)]
        if d["is_change_active"]:
            # changes/active 用 created 当 last_updated（兼容 date 字段）
            if not (fields.get("created") or fields.get("date") or fields.get("last_updated")):
                missing.append("created")
        if missing:
            alerts.append(("ALERT", rel, f"缺必备字段: {', '.join(missing)}"))
        if d["is_change_active"]:
            eff = parse_date(fields.get("created") or fields.get("date") or fields.get("last_updated"))
        else:
            eff = parse_date(fields.get("last_updated"))
        d["effective_updated"] = eff

        status = fields.get("status", "")
        # 规则 b
        if status == "active" and eff and (today - eff).days > STALE_DAYS:
            alerts.append(("STALE", rel,
                           f"status=active 且 last_updated={eff.isoformat()} 超 {STALE_DAYS} 天（{(today - eff).days} 天）"))

        # 规则 c：反引号代码路径漂移
        if eff:
            drifted = []
            for m in BACKTICK_PATH.finditer(d["body"]):
                cand = m.group(1).strip()
                if "/" not in cand or cand.startswith("http"):
                    continue
                if not ("/src/" in cand or cand.startswith("src/")
                        or re.search(r"\.(java|py|sql|xml|ya?ml|properties|json)$", cand)):
                    continue
                target = (ROOT / cand)
                try:
                    if target.is_file():
                        mtime = datetime.date.fromtimestamp(target.stat().st_mtime)
                        if mtime > eff:
                            drifted.append(f"{cand} (代码 {mtime.isoformat()} > 文档 {eff.isoformat()})")
                except OSError:
                    continue
            if drifted:
                alerts.append(("DRIFT-STALE", rel,
                               "引用代码路径晚于 last_updated: " + "; ".join(sorted(set(drifted))[:5])))

    # 规则 d：deprecated 文档仍被 active 文档引用
    deprecated = {d["rel"]: d for d in scanned
                  if d["fields"] and d["fields"].get("status") == "deprecated"}
    if deprecated:
        for d in scanned:
            if not d["fields"] or d["fields"].get("status") != "active":
                continue
            for m in MD_LINK.finditer(d["body"]):
                target = (d["path"].parent / m.group(1)).resolve()
                try:
                    t_rel = target.relative_to(HARNESS).as_posix()
                except ValueError:
                    continue
                if t_rel in deprecated:
                    alerts.append(("ALERT", deprecated[t_rel]["rel"],
                                   f"status=deprecated 但仍被 active 文档 {d['rel']} 引用"))

    n_alert = sum(1 for a in alerts if a[0] == "ALERT")
    n_stale = sum(1 for a in alerts if a[0] == "STALE")
    n_drift = sum(1 for a in alerts if a[0] == "DRIFT-STALE")
    stale_rate = (n_stale + n_drift) / len(scanned) * 100 if scanned else 0.0

    lines = ["# 文档健康度报告", "",
             "> 生成：`python .harness/tools/doc_freshness_scan.py`（脚本产物，豁免 frontmatter）",
             f"> 生成日期：{today.isoformat()}", "",
             "## 健康度总览", "",
             "| 指标 | 数值 |",
             "|------|------|",
             f"| .harness 文档总数 | {len(docs)} |",
             f"| 豁免文档 | {len(exempted)} |",
             f"| 受检文档 | {len(scanned)} |",
             f"| ALERT | {n_alert} |",
             f"| STALE | {n_stale} |",
             f"| DRIFT-STALE | {n_drift} |",
             f"| stale 率 | {stale_rate:.1f}% |",
             "",
             "## 分级明细", "",
             "| 级别 | 文档 | 说明 |",
             "|------|------|------|"]
    for level, rel, detail in sorted(alerts, key=lambda x: (x[0], x[1])):
        lines.append(f"| {level} | {rel} | {detail} |")
    if not alerts:
        lines.append("| - | - | （无告警） |")
    lines.append("")
    lines.append("## 豁免清单")
    lines.append("")
    for rel, reason in exempted:
        lines.append(f"- `{rel}` — {reason}")
    lines.append("")

    # 保留 SECTION 标记及其后内容
    tail = ""
    if OUT.exists():
        old = OUT.read_text(encoding="utf-8")
        idxs = [old.find(mk) for mk in SECTION_MARKERS if old.find(mk) >= 0]
        if idxs:
            tail = old[min(idxs):].rstrip("\n")
    if not tail:
        tail = ("\n".join([
            SECTION_MARKERS[0], "",
            "（待 `doc_link_check.py` 写入）", "",
            SECTION_MARKERS[1], "",
            "（待 `doc_drift_scan.py` 写入）",
        ]))
    lines.append(tail)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"docs={len(docs)} exempted={len(exempted)} checked={len(scanned)}")
    print(f"ALERT={n_alert} STALE={n_stale} DRIFT-STALE={n_drift} stale_rate={stale_rate:.1f}%")
    for level, rel, detail in alerts:
        print(f"[{level}] {rel} — {detail}")
    print(f"report={OUT}")
    sys.exit(0)


if __name__ == "__main__":
    main()
