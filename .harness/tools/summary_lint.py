# -*- coding: utf-8 -*-
"""summary_lint — 需求分析报告机械检查器 v2（蓝军 R9 的确定性半边 + 矩阵生成）。

用法：python tools/summary_lint.py .harness/requests/{需求名}/summary.md
输出：控制台 + {报告同目录}/_review/lint-report.md；存在 CRITICAL 退出码 1。

机械检查项：
  L1 状态机成功终态（CRITICAL）
  L2 死状态（MAJOR）
  L3 同状态多出边（MINOR，提示语义复核）
  L4 映射表锚点：章节号存在 + 关键词匹配标题（CRITICAL）
  L5 规则引用 BR-xx 必须有定义（MAJOR）
  L6 表读写矩阵：每张表至少一处写（CRITICAL）/一处读（MINOR）
  L7 映射表行 vs alignment-log Q 编号覆盖：每个 Q 必须有映射行（MAJOR）
  L8 [🟡待澄清] 降级项必须附人类确认记录（MINOR）

矩阵生成（蓝军只填判断列，禁止手建）：
  矩阵① 转移清单  矩阵② 表读写矩阵  矩阵③ 引用核对清单
"""
import re
import sys
from pathlib import Path

KW_MAP = {
    "时序图": ["时序", "流程"],
    "决策表": ["决策", "规则"],
    "Redis": ["Redis", "缓存"],
    "状态机": ["状态机", "状态"],
    "数据模型": ["数据模型"],
}
WRITE_KW = ("INSERT", "UPDATE", "save", "写入", "落库", "DELETE")
READ_KW = ("SELECT", "查询", "find", "query", "Query")


def lint(summary_path: Path):
    text = summary_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    findings = []

    # ---- mermaid 块 ----
    blocks, cur, in_block = [], [], False
    for ln in lines:
        if ln.strip().startswith("```mermaid"):
            in_block, cur = True, []
        elif in_block and ln.strip().startswith("```"):
            blocks.append("\n".join(cur))
            in_block = False
        elif in_block:
            cur.append(ln)

    # ---- 状态机边 ----
    edges = []  # (src, dst, event, actions)
    for b in blocks:
        if "stateDiagram" in b:
            for m in re.finditer(r"^\s*(\[\*\]|[A-Za-z_][\w]*)\s*-->\s*(\[\*\]|[A-Za-z_][\w]*)\s*:?\s*(.*)$", b, re.M):
                label = m.group(3).strip()
                em = re.match(r"([^(]+)(?:\(([^)]*)\))?", label)
                edges.append((m.group(1), m.group(2),
                              (em.group(1).strip() if em else label),
                              (em.group(2).strip() if em and em.group(2) else "")))

    if edges:
        states = {s for s, _, _, _ in edges if s != "[*]"} | {t for _, t, _, _ in edges if t != "[*]"}
        if not any(re.search(r"FINISH|SUCCESS|DONE|COMPLETE", s) for s in states):
            findings.append(("CRITICAL", "L1", f"状态机无成功终态（现有状态：{', '.join(sorted(states))}）"))
        out_map = {}
        for s, t, _, _ in edges:
            out_map.setdefault(s, set()).add(t)
        for st in sorted(states):
            outs = out_map.get(st, set())
            if not outs:
                findings.append(("MAJOR", "L2", f"死状态 {st}：无出边且未流向 [*]"))
            real = outs - {st}
            if len(real) > 1:
                findings.append(("MINOR", "L3", f"状态 {st} 有 {len(real)} 条出边（→{', →'.join(sorted(real))}），需人工确认触发条件可区分"))

    # ---- 章节 ----
    sections = {}
    for ln in lines:
        m = re.match(r"^#{2,3}\s*(\d+(?:\.\d+)?)[\.、\s]+(.+)$", ln)
        if m:
            sections[m.group(1)] = m.group(2).strip()

    # ---- 映射表 ----
    map_rows, in_map = [], False
    for ln in lines:
        if "意图注入映射表" in ln:
            in_map = True
            continue
        if in_map and ln.startswith("#"):
            in_map = False
        if in_map and ln.strip().startswith("|"):
            map_rows.append(ln)

    anchors = []  # (ref, verdict)
    for ln in map_rows:
        for m in re.finditer(r"§(\d+(?:\.\d+)?)\s*([^\s，。；|]*)", ln):
            num, kw = m.group(1), m.group(2)
            if num not in sections:
                verdict = f"❌ §{num} 不存在"
                findings.append(("CRITICAL", "L4", f"映射表引用 §{num}（{kw}）——该章节不存在"))
            else:
                bad = False
                for key, targets in KW_MAP.items():
                    if key in kw and not any(t in sections[num] for t in targets):
                        verdict = f"❌ §{num} 标题为「{sections[num]}」"
                        findings.append(("CRITICAL", "L4", f"映射表引用「§{num} {kw}」，但 §{num} 标题为「{sections[num]}」，锚点错位"))
                        bad = True
                        break
                if not bad:
                    verdict = f"✅ §{num} {sections[num]}"
            anchors.append((f"§{num} {kw}".strip(), verdict))

    # ---- L5 ----
    defined = set(re.findall(r"BR-(\d+)", "\n".join(ln for ln in lines if ln.startswith("| BR"))))
    for r in sorted(set(re.findall(r"BR-(\d+)", text)) - defined):
        findings.append(("MAJOR", "L5", f"引用了 BR-{r} 但决策表中无定义"))

    # ---- L6 表读写 ----
    sql_dir = summary_path.parent.parent.parent.parent / "sql"
    if not sql_dir.exists():
        sql_dir = summary_path.parent / "sql"
    table_matrix = []  # (table, writers, readers)
    for sql in sorted(sql_dir.glob("*.sql")) if sql_dir.exists() else []:
        for tm in re.finditer(r"CREATE TABLE[^`]*`(\w+)`", sql.read_text(encoding="utf-8")):
            tbl = tm.group(1)
            tbl_lines = [ln.strip() for ln in text.split("\n") if tbl in ln]
            writers = [ln[:60] for ln in tbl_lines if any(w in ln for w in WRITE_KW)]
            readers = [ln[:60] for ln in tbl_lines if any(r in ln for r in READ_KW)]
            table_matrix.append((tbl, writers, readers))
            if not writers:
                findings.append(("CRITICAL", "L6", f"表 {tbl} 全报告无任何写入动作（图/文均无 INSERT/UPDATE/save）"))
            if not readers:
                findings.append(("MINOR", "L6", f"表 {tbl} 全报告无读取动作"))

    # ---- L7 映射行 vs 日志 Q 覆盖 ----
    log_path = summary_path.parent / "_review" / "alignment-log.md"
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8")
        q_nums = set(re.findall(r"^## Q(\d+)", log_text, re.M))
        map_nums = set()
        for ln in map_rows:
            m = re.match(r"\s*\|\s*(\d+)", ln)
            if m:
                map_nums.add(m.group(1))
        for q in sorted(q_nums - map_nums, key=int):
            findings.append(("MAJOR", "L7", f"alignment-log Q{q} 在意图注入映射表中无对应行（注入可能未登记落点）"))

    # ---- L8 降级回执 ----
    if "[🟡待澄清]" in text:
        seg_start = text.find("[🟡待澄清]")
        seg = text[seg_start:seg_start + 3000]
        if "确认" not in seg and "同意降级" not in seg:
            findings.append(("MINOR", "L8", "存在 [🟡待澄清] 降级项，但附近未发现人类确认记录字样"))

    return findings, edges, table_matrix, anchors, sections


def main():
    if len(sys.argv) < 2:
        print("usage: python .harness/tools/summary_lint.py <summary.md>")
        sys.exit(2)
    summary_path = Path(sys.argv[1])
    findings, edges, table_matrix, anchors, sections = lint(summary_path)
    crit = [f for f in findings if f[0] == "CRITICAL"]

    rep = ["# summary_lint 机械检查报告（v2）", "",
           f"> 对象：{summary_path.name} | CRITICAL {len(crit)} / 共 {len(findings)} 条",
           "> 生成：python tools/summary_lint.py（机械检查+矩阵骨架，判断列归蓝军）", "",
           "## Findings", ""]
    for lv, rule, detail in findings:
        rep.append(f"- **[{lv}][{rule}]** {detail}")
    if not findings:
        rep.append("（无发现）")

    rep += ["", "## 矩阵① 状态机转移清单", "",
            "| 转移 | 触发事件 | 技术动作 | 时序图对应步骤（蓝军填） | 决策表规则（蓝军填） | 问题（蓝军填） |",
            "|------|---------|---------|----------------------|--------------------|--------------|"]
    for s, t, ev, act in edges:
        rep.append(f"| `{s} → {t}` | {ev} | {act} | 待核 | 待核 | — |")

    rep += ["", "## 矩阵② 表读写矩阵", "",
            "| 表 | 写入动作 | 读取动作 | 权威数据源（蓝军填） | 问题（蓝军填） |",
            "|----|---------|---------|--------------------|--------------|"]
    for tbl, writers, readers in table_matrix:
        w = "<br>".join(writers) if writers else "**无**"
        r = "<br>".join(readers) if readers else "无"
        rep.append(f"| `{tbl}` | {w} | {r} | 待核 | — |")

    rep += ["", "## 矩阵③ 引用核对清单", "",
            "| 落点引用 | 核对结果 |", "|---------|---------|"]
    for ref, verdict in anchors:
        rep.append(f"| {ref} | {verdict} |")

    out = summary_path.parent / "_review" / "lint-report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(rep), encoding="utf-8")

    print(f"CRITICAL={len(crit)} TOTAL={len(findings)} edges={len(edges)} tables={len(table_matrix)} anchors={len(anchors)}")
    for lv, rule, detail in findings:
        print(f"[{lv}][{rule}] {detail}")
    print(f"report={out}")
    sys.exit(1 if crit else 0)


if __name__ == "__main__":
    main()
