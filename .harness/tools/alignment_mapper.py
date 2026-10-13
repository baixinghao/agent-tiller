# -*- coding: utf-8 -*-
"""alignment_mapper — 意图注入映射表草稿生成器（红军减负工具）。

用法：python .harness/tools/alignment_mapper.py .harness/requests/{需求名}/summary.md
输入：{同目录}/_review/alignment-log.md + summary.md
输出：{同目录}/_review/mapping-draft.md

价值：映射表的落点引用（章节号/规则号/步骤）由脚本**真实定位**，
锚点错位（手写 §6 其实是 §5.3 那类事故）在生成侧绝育；
红军只需补/审语义列，禁止凭空手写章节号。
"""
import re
import sys
from pathlib import Path

STOP = {"步骤", "转移", "规则", "决策表", "时序图", "状态机", "字段", "初始化", "提交"}


def parse_log(log_path: Path):
    qs = []
    if not log_path.exists():
        return qs
    text = log_path.read_text(encoding="utf-8")
    for m in re.finditer(r"^## (Q\d+)[^\n]*\n(.*?)(?=^## Q|\Z)", text, re.M | re.S):
        body = m.group(2)
        intent = re.search(r"注入解读：(.+)", body)
        spot = re.search(r"落点：(.+)", body)
        qs.append({
            "q": m.group(1),
            "intent": intent.group(1).strip() if intent else "",
            "spot": spot.group(1).strip() if spot else "",
        })
    return qs


def parse_summary(text: str):
    sections = {}  # num -> title
    for ln in text.split("\n"):
        m = re.match(r"^(#{2,3})\s*(\d+(?:\.\d+)?)[\.、\s]+(.+)$", ln)
        if m:
            sections[m.group(2)] = m.group(3).strip()
    # BR 规则号 -> 定义所在章节（仅认决策表定义行 "| BR-xx"，忽略引用行）
    br_sec = {}
    cur_sec = "?"
    for ln in text.split("\n"):
        h = re.match(r"^#{2,3}\s*(\d+(?:\.\d+)?)", ln)
        if h:
            cur_sec = h.group(1)
        if ln.strip().startswith("| BR"):
            for br in re.findall(r"BR-\d+", ln):
                br_sec.setdefault(br, cur_sec)
    # mermaid 行 -> (类型, 序号/描述)
    mermaid_hits = []  # (kind, label, line_text)
    in_block, kind, step = False, "", 0
    for ln in text.split("\n"):
        if ln.strip().startswith("```mermaid"):
            in_block, kind, step = True, "", 0
            continue
        if in_block and ln.strip().startswith("```"):
            in_block = False
            continue
        if in_block:
            if "stateDiagram" in ln:
                kind = "状态机"
            elif "sequenceDiagram" in ln:
                kind = "时序图"
            if "->>" in ln:
                step += 1
                mermaid_hits.append((kind, f"步骤 {step}", ln.strip()))
            elif "-->" in ln:
                mermaid_hits.append((kind, "转移", ln.strip()))
    return sections, br_sec, mermaid_hits


def locate(fragment: str, sections, br_sec, mermaid_hits):
    """为一个落点片段找真实锚点。"""
    hits = []
    # 显式 BR-xx
    for br in re.findall(r"BR-\d+", fragment):
        if br in br_sec:
            hits.append(f"§{br_sec[br]} {br}")
    # 显式 §x.y
    for s in re.findall(r"§(\d+(?:\.\d+)?)", fragment):
        if s in sections:
            hits.append(f"§{s} {sections[s]}")
    # 标识符（CamelCase / snake_case / 缓存 key 形如 prefix:xxx）
    for tok in re.findall(r"[A-Za-z_][\w.:{}]*", fragment):
        if len(tok) < 4 or tok in ("BR",):
            continue
        for kind, label, line in mermaid_hits:
            if tok in line:
                hits.append(f"{kind}{label}（{line[:48]}…）" if len(line) > 48 else f"{kind}{label}（{line}）")
                break
    # 中文片段（≥4 字）
    for zh in re.findall(r"[一-鿿]{4,}", fragment):
        if zh in STOP:
            continue
        for kind, label, line in mermaid_hits:
            if zh in line:
                hits.append(f"{kind}{label}（{line[:48]}…）" if len(line) > 48 else f"{kind}{label}（{line}）")
                break
    return list(dict.fromkeys(hits))  # 去重保序


def main():
    if len(sys.argv) < 2:
        print("usage: python .harness/tools/alignment_mapper.py <summary.md>")
        sys.exit(2)
    summary_path = Path(sys.argv[1])
    text = summary_path.read_text(encoding="utf-8")
    log_path = summary_path.parent / "_review" / "alignment-log.md"
    qs = parse_log(log_path)
    if not qs:
        print("未找到 alignment-log.md 或无 Q 记录")
        sys.exit(1)
    sections, br_sec, mermaid_hits = parse_summary(text)

    out = ["# 意图注入映射表 — 草稿（alignment_mapper 生成）", "",
           "> 落点由脚本真实定位（存在性保证）；红军复核语义后并入 summary.md §1.4。",
           "> 生成：python .harness/tools/alignment_mapper.py", "",
           "| # | 注入的意图 | 落点（脚本定位） | 复核（红军填） |",
           "|---|-----------|-----------------|---------------|"]
    unresolved = 0
    for q in qs:
        spots = []
        for frag in re.split(r"[；;、]", q["spot"]):
            frag = frag.strip()
            if frag:
                spots.extend(locate(frag, sections, br_sec, mermaid_hits))
        spots = list(dict.fromkeys(spots))
        if not spots:
            unresolved += 1
            spots = ["⚠️ 未定位（红军手填）"]
        intent = q["intent"][:60] + ("…" if len(q["intent"]) > 60 else "")
        out.append(f"| {q['q'][1:]} | {intent} | {'<br>'.join(spots)} | — |")

    out_path = summary_path.parent / "_review" / "mapping-draft.md"
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Q={len(qs)} unresolved={unresolved}")
    print(f"draft={out_path}")


if __name__ == "__main__":
    main()
