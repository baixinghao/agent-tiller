# -*- coding: utf-8 -*-
"""文档↔代码漂移扫描（轻量版）。

从 .harness/wiki/*.md 和 .harness/specs/*.md 提取：
  a) 反引号内形如 com.xxx.yyy.Zzz 的全限定类名
     -> 在仓库 .java 中 grep 是否存在对应 class/interface/enum/record Zzz
  b) 反引号内形如 /xxx/yyy 的 API 路径
     -> grep 代码中 @RequestMapping/@GetMapping 等注解的 value 是否存在

不存在的记为漂移项，写入 .harness/index/DOC_HEALTH.md 的 <!-- SECTION:DRIFT --> 区块
（替换该标记到文件尾之间的旧内容）。
退出码：始终 0（报告型）。
"""
import datetime
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".harness"
DOC_HEALTH = HARNESS / "index" / "DOC_HEALTH.md"

MARKER = "<!-- SECTION:DRIFT -->"

BACKTICK = re.compile(r"`([^`\n]+)`")
FQCN = re.compile(r"^com\.[\w.]+?\.([A-Z][A-Za-z0-9_]*)$")
API_PATH = re.compile(r"^/[a-zA-Z0-9_\-{}]+(?:/[a-zA-Z0-9_\-{}]+)+$")
# wiki 常见写法：表格中 `POST /api/xxx/yyy` 裸文本（非反引号）
BARE_API = re.compile(r"\b(?:POST|GET|PUT|DELETE|PATCH)\s+(/[a-zA-Z0-9_\-{}]+(?:/[a-zA-Z0-9_\-{}]+)+)")
TYPE_DECL = re.compile(r"\b(class|interface|enum|record)\s+([A-Z][A-Za-z0-9_]*)")
MAPPING = re.compile(r"@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)")


def build_corpus():
    """收集仓库全部 .java 源码文本 + 其中声明的类型名 + 出现的 API 路径片段。"""
    type_names = set()
    api_fragments = set()
    for module_dir in ROOT.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith("."):
            continue
        src = module_dir / "src" / "main" / "java"
        if not src.is_dir():
            continue
        for jf in src.rglob("*.java"):
            text = jf.read_text(encoding="utf-8", errors="replace")
            for m in TYPE_DECL.finditer(text):
                type_names.add(m.group(2))
            # mapping 注解 value 中的路径
            for mm in re.finditer(
                    r"@(?:RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)"
                    r"\s*\(([^)]*)\)", text):
                for s in re.findall(r'"([^"]+)"', mm.group(1)):
                    api_fragments.add(s.strip())
    return type_names, api_fragments


def api_exists(path, fragments):
    """API 路径存在性：任一 mapping value 以该路径结尾或等于之（类级+方法级拼接场景）。"""
    for frag in fragments:
        if frag == path or path.endswith(frag) or frag.endswith(path):
            return True
    return False


def main():
    type_names, api_fragments = build_corpus()

    drift = []  # (doc, kind, item)
    checked_fqcn = 0
    checked_api = 0
    docs = sorted(HARNESS.glob("wiki/*.md")) + sorted(HARNESS.glob("specs/*.md"))
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        seen = set()
        for m in BACKTICK.finditer(text):
            item = m.group(1).strip()
            fm = FQCN.match(item)
            if fm:
                checked_fqcn += 1
                if fm.group(1) not in type_names:
                    drift.append((doc.relative_to(ROOT).as_posix(), "类名", item))
                continue
            if API_PATH.match(item):
                checked_api += 1
                seen.add(item)
        # 裸 API 路径（POST /api/xxx 表格写法）
        for m in BARE_API.finditer(text):
            seen.add(m.group(1))
            checked_api += 1
        for item in sorted(seen):
            if not api_exists(item, api_fragments):
                drift.append((doc.relative_to(ROOT).as_posix(), "API 路径", item))

    today = datetime.date.today().isoformat()
    lines = [f"> 生成：`python .harness/tools/doc_drift_scan.py`（{today}）", "",
             f"- 检查全限定类名：{checked_fqcn} 个引用",
             f"- 检查 API 路径：{checked_api} 个引用",
             f"- 漂移项：{len(drift)}", ""]
    if drift:
        lines += ["| 文档 | 类型 | 漂移项 |", "|------|------|--------|"]
        for doc, kind, item in drift:
            lines.append(f"| {doc} | {kind} | `{item}` |")
    else:
        lines.append("（无漂移 ✅）")

    # 替换 DRIFT 区块（到文件尾）
    if DOC_HEALTH.exists():
        text = DOC_HEALTH.read_text(encoding="utf-8")
    else:
        text = "# 文档健康度报告\n\n" + MARKER + "\n"
    start = text.find(MARKER)
    if start < 0:
        text = text.rstrip("\n") + "\n\n" + MARKER + "\n"
        start = text.find(MARKER)
    after = start + len(MARKER)
    new = text[:after] + "\n\n" + "\n".join(lines) + "\n"
    DOC_HEALTH.write_text(new, encoding="utf-8")

    print(f"fqcn={checked_fqcn} api={checked_api} drift={len(drift)}")
    for doc, kind, item in drift:
        print(f"[DRIFT][{kind}] {doc} -> {item}")
    print(f"updated={DOC_HEALTH}")
    sys.exit(0)


if __name__ == "__main__":
    main()
