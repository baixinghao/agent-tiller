# -*- coding: utf-8 -*-
"""Build an AST index tree for ALL maven modules using tree-sitter Java.

自动发现 ROOT 下所有含 src/main/java 的一级目录作为模块，逐模块解析。

内部包前缀（用于区分项目内 import 与第三方 import）：
  - 默认自动推断：全部文件包名中出现次数最多的前 3 段（如 com.example）
  - 可用环境变量 HARNESS_INTERNAL_PREFIX 显式覆盖

Outputs:
  .harness/index/ast_index.json  - {"modules": {模块名: {"packages": {...}}}}
  .harness/index/AST_INDEX.md    - human/agent-readable tree（按模块分节）
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_java

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / ".harness" / "index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANG = Language(tree_sitter_java.language())
parser = Parser(LANG)

LAYER_BY_PKG = [
    ("interfaces", "interfaces"),
    ("application", "application"),
    ("domain.policy", "domain/policy"),
    ("domain.service", "domain/service"),
    ("domain.acl", "domain/acl"),
    ("domain.gateway", "domain/gateway"),
    ("domain.repository", "domain/repository"),
    ("domain.model", "domain/model"),
    ("domain", "domain"),
    ("infrastructure", "infrastructure"),
]


def node_text(node, src):
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def layer_of(package: str) -> str:
    for key, layer in LAYER_BY_PKG:
        if f".{key}" in package or package.endswith(key.split(".")[-1]):
            return layer
    return "other"


def parse_file(path: Path):
    src = path.read_bytes()
    tree = parser.parse(src)
    root = tree.root_node

    package = ""
    imports = []
    types = []

    for child in root.children:
        if child.type == "package_declaration":
            package = node_text(child, src).replace("package", "").replace(";", "").strip()
        elif child.type == "import_declaration":
            imp = node_text(child, src).replace("import", "").replace(";", "").strip()
            imports.append(imp)
        elif child.type in ("class_declaration", "interface_declaration",
                            "enum_declaration", "record_declaration", "annotation_type_declaration"):
            types.append(extract_type(child, src))

    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "package": package,
        "imports_all": imports,
        "types": types,
    }


def extract_type(node, src):
    kind = node.type.replace("_declaration", "")
    name = ""
    annotations = []
    extends = []
    implements = []
    methods = []
    fields = []

    for child in node.children:
        if child.type == "modifiers":
            for m in child.children:
                if m.type in ("marker_annotation", "annotation"):
                    annotations.append(node_text(m, src).split("(")[0].lstrip("@"))
        elif child.type == "identifier":
            name = node_text(child, src)
        elif child.type == "superclass":
            extends.append(node_text(child, src).replace("extends", "").strip())
        elif child.type in ("super_interfaces", "extends_interfaces"):
            implements.append(node_text(child, src)
                              .replace("implements", "").replace("extends", "").strip())
        elif child.type in ("class_body", "interface_body", "enum_body", "annotation_type_body"):
            for member in child.children:
                if member.type == "method_declaration":
                    methods.append(extract_method(member, src))
                elif member.type in ("field_declaration", "constant_declaration"):
                    fields.append(extract_field(member, src))
                elif member.type in ("class_declaration", "interface_declaration",
                                     "enum_declaration", "record_declaration"):
                    # nested type, keep flat under parent name
                    nested = extract_type(member, src)
                    nested["name"] = None  # marker; caller prefixes
                    methods.append({"name": f"<nested:{nested.get('name') or '?'}>",
                                    "signature": "", "annotations": []})

    return {
        "kind": kind,
        "name": name,
        "annotations": annotations,
        "extends": extends,
        "implements": implements,
        "methods": methods,
        "fields": fields,
    }


def extract_method(node, src):
    name = ""
    ret = ""
    params = ""
    annotations = []
    for child in node.children:
        if child.type == "modifiers":
            for m in child.children:
                if m.type in ("marker_annotation", "annotation"):
                    annotations.append(node_text(m, src).split("(")[0].lstrip("@"))
        elif child.type == "identifier":
            name = node_text(child, src)
        elif child.type in ("type_identifier", "void_type", "integral_type",
                            "floating_point_type", "boolean_type", "generic_type"):
            if not ret:
                ret = node_text(child, src)
        elif child.type == "formal_parameters":
            raw = node_text(child, src)
            # compress param list to types only
            inner = raw.strip()[1:-1].strip()
            if not inner:
                params = "()"
            else:
                parts = [p.strip() for p in split_params(inner)]
                sig = []
                for p in parts:
                    tokens = p.split()
                    # drop parameter name (last token) unless single token
                    sig.append(" ".join(tokens[:-1]) if len(tokens) > 1 else tokens[0])
                params = "(" + ", ".join(sig) + ")"
    return {"name": name, "signature": f"{ret} {name}{params}".strip(), "annotations": annotations,
            "line_start": node.start_point[0] + 1, "line_end": node.end_point[0] + 1}


def split_params(s):
    """Split top-level commas, ignoring generics <>."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts


def extract_field(node, src):
    text = node_text(node, src).rstrip(";").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:120]


def discover_modules():
    """自动发现 ROOT 下所有含 src/main/java 的一级目录作为模块。"""
    modules = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if (d / "src" / "main" / "java").is_dir():
            modules.append(d.name)
    return modules


def detect_internal_prefix(all_packages):
    """推断内部包前缀：HARNESS_INTERNAL_PREFIX 环境变量优先，
    否则取全部包名中出现次数最多的前 3 段（如 com.example）。"""
    env = os.environ.get("HARNESS_INTERNAL_PREFIX", "").strip()
    if env:
        return env
    counter = Counter()
    for pkg in all_packages:
        parts = pkg.split(".")
        if len(parts) >= 3:
            counter[".".join(parts[:3])] += 1
    return counter.most_common(1)[0][0] if counter else None


def main():
    modules = discover_modules()
    modules_data = {}
    total_files = 0

    # 第一遍：解析全部模块
    for module in modules:
        src = ROOT / module / "src" / "main"
        files = sorted(src.rglob("*.java"))
        entries = [parse_file(f) for f in files]
        total_files += len(files)

        # group by package
        packages = {}
        for e in entries:
            packages.setdefault(e["package"], []).append(e)
        modules_data[module] = {"packages": packages}

    # 内部包前缀判定（imports_internal 供合规检查区分项目内/第三方依赖）
    all_packages = [pkg for m in modules_data.values() for pkg in m["packages"]]
    prefix = detect_internal_prefix(all_packages)
    for m in modules_data.values():
        for entries in m["packages"].values():
            for e in entries:
                e["imports_internal"] = ([i for i in e["imports_all"] if i.startswith(prefix)]
                                         if prefix else [])

    lines = ["# AST 索引树",
             "",
             f"> 由 tree-sitter-java 生成，覆盖模块：{', '.join(modules)}。",
             f"> 内部包前缀：{prefix or '(未识别)'}",
             "> 重新生成：`python .harness/tools/build_ast_index.py`",
             ""]

    # 第二遍：渲染 Markdown
    for module in modules:
        packages = modules_data[module]["packages"]

        lines.append(f"## 模块 `{module}`（{sum(len(v) for v in packages.values())} 个 Java 文件，{len(packages)} 个包）")
        lines.append("")
        # dependency edges between layers
        edges = {}
        for entries in packages.values():
            for e in entries:
                src_layer = layer_of(e["package"])
                for imp in e["imports_internal"]:
                    dst_pkg = imp.rsplit(".", 1)[0]
                    dst_layer = layer_of(dst_pkg)
                    if dst_layer != src_layer:
                        edges.setdefault(f"{src_layer} -> {dst_layer}", set()).add(
                            f"{e['package']} 引用 {imp}")

        lines.append(f"### 层间依赖边（import 级）— {module}")
        lines.append("")
        for k in sorted(edges):
            lines.append(f"- **{k}** ({len(edges[k])} 条 import)")
        lines.append("")

        lines.append(f"### 包树 — {module}")
        lines.append("")
        for pkg in sorted(packages):
            layer = layer_of(pkg)
            lines.append(f"#### `{pkg}`  [{layer}]")
            lines.append("")
            for e in sorted(packages[pkg], key=lambda x: x["file"]):
                for t in e["types"]:
                    anns = (" @" + ",@".join(t["annotations"])) if t["annotations"] else ""
                    ext = f" extends {','.join(t['extends'])}" if t["extends"] else ""
                    impl = f" implements {','.join(t['implements'])}" if t["implements"] else ""
                    lines.append(f"- **{t['kind']} `{t['name']}`**{anns}{ext}{impl}")
                    for m in t["methods"]:
                        mann = (" @" + ",@".join(m["annotations"])) if m["annotations"] else ""
                        lines.append(f"  - {m['signature']}{mann}")
            lines.append("")

    json_path = OUT_DIR / "ast_index.json"
    json_path.write_text(json.dumps({"modules": modules_data}, ensure_ascii=False, indent=1),
                         encoding="utf-8")

    md_path = OUT_DIR / "AST_INDEX.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"modules={len(modules)} files={total_files} internal_prefix={prefix}")
    for m in modules:
        print(f"  {m}: files={sum(len(v) for v in modules_data[m]['packages'].values())} packages={len(modules_data[m]['packages'])}")
    print(f"json={json_path}")
    print(f"md={md_path} ({md_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
