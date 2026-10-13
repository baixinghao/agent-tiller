# -*- coding: utf-8 -*-
"""文档死链与索引一致性检查。

检查范围：.harness/**/*.md + CLAUDE.md（根目录或 .claude/，两种布局皆兼容）+ 根 AGENTS.md
  1. 所有 markdown 相对链接可解析（锚点 # 后部分忽略）-> 死链列表
  2. C1 一致性：.harness/specs/README.md 若有索引表，对照 specs/ 实际目录
     （无索引表则跳过并注明）

结果写入 .harness/index/DOC_HEALTH.md 的 <!-- SECTION:LINK_CHECK --> 区块
（替换该标记到下一个 SECTION 标记或文件尾之间的旧内容）。
退出码：始终 0（报告型）。
"""
import datetime
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".harness"
DOC_HEALTH = HARNESS / "index" / "DOC_HEALTH.md"

MARKER = "<!-- SECTION:LINK_CHECK -->"
OTHER_MARKERS = ("<!-- SECTION:DRIFT -->",)

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TABLE_LINK = re.compile(r"^\|.*\]\(([^)\s]+)\).*\|")


def collect_targets():
    docs = sorted(HARNESS.rglob("*.md"))
    for extra in (ROOT / "CLAUDE.md", ROOT / ".claude" / "CLAUDE.md", ROOT / "AGENTS.md"):
        if extra.exists():
            docs.append(extra)
    return docs


def check_links():
    dead = []
    total = 0
    for doc in collect_targets():
        text = doc.read_text(encoding="utf-8")
        for m in MD_LINK.finditer(text):
            raw = m.group(1)
            target = unquote(raw.split("#", 1)[0]).strip()
            if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue  # http(s)/mailto 等外部链接
            total += 1
            # 兼容两种约定：相对文档目录 或 相对仓库根（CLAUDE.md/AGENTS.md 用后者）
            if (doc.parent / target).resolve().exists() or (ROOT / target).resolve().exists():
                continue
            dead.append((doc.relative_to(ROOT).as_posix(), raw))
    return total, dead


def check_specs_index():
    """对照 specs/README.md 索引表与 specs/ 实际目录。返回 (lines, skipped)。"""
    readme = HARNESS / "specs" / "README.md"
    specs = HARNESS / "specs"
    if not readme.exists():
        return ["- specs/README.md 不存在，跳过索引一致性检查"], True
    indexed = set()
    has_table = False
    for line in readme.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        for m in TABLE_LINK.finditer(line):
            target = m.group(1).split("#", 1)[0].strip()
            if not target or ":" in target:
                continue
            if (readme.parent / target).resolve().parent != specs.resolve() \
                    and target.startswith(("..", "/")):
                continue
            has_table = True
            indexed.add(target.rstrip("/"))
    if not has_table:
        return ["- specs/README.md 无索引表，跳过索引一致性检查（已注明）"], True
    actual = {p.name for p in specs.iterdir()
              if p.name != "README.md" and (p.is_dir() or p.suffix == ".md")}
    problems = []
    for name in sorted(indexed - actual):
        problems.append(f"- 索引表引用 `{name}` 但 specs/ 下不存在")
    for name in sorted(actual - indexed):
        problems.append(f"- specs/{name} 存在但未在索引表登记")
    if not problems:
        problems.append("- specs/README.md 索引表与 specs/ 目录一致 ✅")
    return problems, False


def write_section(body_lines):
    """替换 DOC_HEALTH.md 中 MARKER 区块的内容。"""
    if DOC_HEALTH.exists():
        text = DOC_HEALTH.read_text(encoding="utf-8")
    else:
        text = "# 文档健康度报告\n\n" + MARKER + "\n\n<!-- SECTION:DRIFT -->\n"
    start = text.find(MARKER)
    if start < 0:
        # 标记不存在：附加到文件尾（在 DRIFT 标记前若有）
        insert_at = len(text)
        for mk in OTHER_MARKERS:
            i = text.find(mk)
            if 0 <= i < insert_at:
                insert_at = i
        text = text[:insert_at].rstrip("\n") + "\n\n" + MARKER + "\n\n" + text[insert_at:]
        start = text.find(MARKER)
    after = start + len(MARKER)
    end = len(text)
    for mk in OTHER_MARKERS:
        i = text.find(mk, after)
        if 0 <= i < end:
            end = i
    new = text[:after] + "\n\n" + "\n".join(body_lines) + "\n\n" + text[end:]
    DOC_HEALTH.write_text(new.rstrip("\n") + "\n", encoding="utf-8")


def main():
    today = datetime.date.today().isoformat()
    total, dead = check_links()
    idx_lines, idx_skipped = check_specs_index()

    lines = [f"> 生成：`python .harness/tools/doc_link_check.py`（{today}）", "",
             "## 死链检查", "",
             f"- 检查相对链接总数：{total}",
             f"- 死链数量：{len(dead)}", ""]
    if dead:
        lines += ["| 文档 | 死链 |", "|------|------|"]
        for doc, raw in dead:
            lines.append(f"| {doc} | `{raw}` |")
    else:
        lines.append("（无死链 ✅）")
    lines += ["", "## specs 索引一致性（C1）", ""] + idx_lines

    write_section(lines)
    print(f"links={total} dead={len(dead)} specs_index_skipped={idx_skipped}")
    for doc, raw in dead:
        print(f"[DEAD] {doc} -> {raw}")
    print(f"updated={DOC_HEALTH}")
    sys.exit(0)


if __name__ == "__main__":
    main()
