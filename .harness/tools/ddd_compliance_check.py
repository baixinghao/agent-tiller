# -*- coding: utf-8 -*-
"""DDD 合规检查器 — 把重构 Step 7 从人工审查变成可执行门禁。

输入：.harness/index/ast_index.json（由 tools/build_ast_index.py 生成，{"modules": {...}}）
输出：控制台摘要 + .harness/index/COMPLIANCE_REPORT.md + .harness/index/compliance_history.jsonl
退出码：存在 CRITICAL 违规 → 1，否则 → 0（WARNING 不阻断）

检查项映射 rules/01_ARCHITECTURE_CONSTRAINTS.md §1：
  C-D5     (CRITICAL) D5 领域层零框架依赖：domain/ 下禁止 @Service/@Component/@Repository
  C-DIR    (CRITICAL) D4 依赖方向：domain 禁止 import application/infrastructure/interfaces
  C-POLICY (CRITICAL) D3 Policy 纯函数：domain/policy 禁止 import ACL/Repository，参数禁含 ACL/Repository 类型
  C-ACL    (CRITICAL) D6 ACL 返回领域值对象：domain/acl 接口方法返回类型必须落在 domain/model（或 JDK 原生）
  W-INFRA-APP (WARNING) 契约归属：infrastructure 不应实现 application 层的契约（D4 建议契约归 domain）
  W-IF-DTO    (WARNING) API 契约面：interfaces/dto 不应直接暴露 domain/model 类型
  W-CTRL-FAT  (WARNING) C4 Controller 极薄：Controller 方法跨度异常（启发式，>10 行）
"""
import datetime
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".harness" / "index" / "ast_index.json"
REPORT = ROOT / ".harness" / "index" / "COMPLIANCE_REPORT.md"
HISTORY = ROOT / ".harness" / "index" / "compliance_history.jsonl"

JAVA_OK = re.compile(r"^(java\.|javax\.|jdk\.)")
PRIMITIVES = {"void", "String", "Long", "Integer", "Boolean", "Double", "Float",
              "int", "long", "boolean", "double", "float", "byte", "short", "char",
              "BigDecimal", "LocalDateTime", "LocalDate", "Date", "Map", "List", "Set"}


def base_types(type_str: str):
    """从类型表达式中提取标识符：List<Foo<Bar>> -> [List, Foo, Bar]"""
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", type_str or "")


def layer_of(package: str) -> str:
    for key, layer in [("interfaces", "interfaces"), ("application", "application"),
                       ("domain", "domain"), ("infrastructure", "infrastructure")]:
        if f".{key}" in package:
            return layer
    return "other"


def main():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    modules = idx.get("modules", {})
    findings = []  # (level, rule, module, file, detail)

    # 预收集 ACL / Repository 接口简单名（用于 Policy 参数检查，跨模块汇总）
    acl_names, repo_names = set(), set()
    for mod, mdata in modules.items():
        for pkg, entries in mdata["packages"].items():
            for e in entries:
                for t in e["types"]:
                    if ".domain.acl" in pkg:
                        acl_names.add(t["name"])
                    if ".domain.repository" in pkg:
                        repo_names.add(t["name"])

    for mod, mdata in modules.items():
        for pkg, entries in mdata["packages"].items():
            layer = layer_of(pkg)
            for e in entries:
                f = e["file"]
                internal = e["imports_internal"]

                # C-DIR: domain 不许依赖其他层
                if layer == "domain":
                    for imp in internal:
                        if any(s in imp for s in (".infrastructure", ".application", ".interfaces")):
                            findings.append(("CRITICAL", "C-DIR", mod, f, f"domain 非法依赖 {imp}"))

                # C-D5: domain 下禁止 Spring 注解
                if layer == "domain":
                    for t in e["types"]:
                        bad = set(t["annotations"]) & {"Service", "Component", "Repository"}
                        if bad:
                            findings.append(("CRITICAL", "C-D5", mod, f,
                                             f"{t['name']} 标注了 @{',@'.join(sorted(bad))}"))

                # C-POLICY: policy 纯度
                if ".domain.policy" in pkg:
                    for imp in internal:
                        if ".acl" in imp or ".repository" in imp or ".infrastructure" in imp:
                            findings.append(("CRITICAL", "C-POLICY", mod, f, f"Policy import 了 {imp}"))
                    for t in e["types"]:
                        for m in t.get("methods", []):
                            params = m.get("signature", "")
                            for name in base_types(params):
                                if name in acl_names or name in repo_names:
                                    findings.append(("CRITICAL", "C-POLICY", mod, f,
                                                     f"{t['name']}.{m['name']} 参数含 {name}"))

                # C-ACL: ACL 返回领域值对象
                if ".domain.acl" in pkg:
                    # 简单名 → import 全限定名（含 JDK import）
                    imp_map = {i.rsplit(".", 1)[-1].replace(";", ""): i
                               for i in e.get("imports_all", e["imports_internal"])}
                    WRAPPERS = {"Optional", "CompletableFuture", "Future", "List", "Set",
                                "Map", "Collection", "Page", "Mono", "Flux"}
                    for t in e["types"]:
                        for m in t.get("methods", []):
                            ret = m.get("signature", "").split(" ", 1)[0] if m.get("signature") else ""
                            for name in base_types(ret):
                                if name in PRIMITIVES or name in WRAPPERS or name == t["name"]:
                                    continue
                                if name == "Object":
                                    findings.append(("CRITICAL", "C-ACL", mod, f,
                                                     f"{t['name']}.{m['name']} 返回裸 Object（违反 D6 领域值对象 / C2 参数强类型）"))
                                    continue
                                full = imp_map.get(name)
                                if full is None:
                                    # 未 import：说明是同文件/同包内定义的类型（如嵌套 record）
                                    findings.append(("CRITICAL", "C-ACL", mod, f,
                                                     f"{t['name']}.{m['name']} 返回 {name}（ACL 包内定义的类型，D6 要求落在 domain/model）"))
                                elif JAVA_OK.match(full):
                                    continue
                                elif ".domain.model" not in full:
                                    findings.append(("CRITICAL", "C-ACL", mod, f,
                                                     f"{t['name']}.{m['name']} 返回 {full}（非 domain/model）"))

                # W-INFRA-APP
                if layer == "infrastructure":
                    for imp in internal:
                        if ".application" in imp:
                            findings.append(("WARNING", "W-INFRA-APP", mod, f,
                                             f"infrastructure 依赖 application 契约 {imp}（建议契约移至 domain）"))

                # W-IF-DTO
                if ".interfaces.dto" in pkg:
                    for imp in internal:
                        if ".domain.model" in imp:
                            findings.append(("WARNING", "W-IF-DTO", mod, f,
                                             f"响应 DTO 直接暴露领域类型 {imp}"))

                # W-CTRL-FAT（启发式：方法定义跨度 > 10 行）
                if ".interfaces.rest" in pkg:
                    for t in e["types"]:
                        for m in t.get("methods", []):
                            ls, le = m.get("line_start"), m.get("line_end")
                            if ls and le and le - ls > 10 and m["name"] != "<init>":
                                findings.append(("WARNING", "W-CTRL-FAT", mod, f,
                                                 f"{t['name']}.{m['name']} 跨度 {le - ls + 1} 行（C4 要求方法体 ≤5 行，请人工复核）"))

    crit = [x for x in findings if x[0] == "CRITICAL"]
    warn = [x for x in findings if x[0] == "WARNING"]

    # ---- 历史趋势（同日重跑覆盖当日行） ----
    today = datetime.date.today().isoformat()
    history = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("date") != today:
                history.append(rec)
    history.append({"date": today, "critical": len(crit), "warning": len(warn)})
    HISTORY.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in history) + "\n",
                       encoding="utf-8")

    lines = ["# DDD 合规检查报告", "",
             "> 生成：`python .harness/tools/ddd_compliance_check.py`（输入：.harness/index/ast_index.json）",
             f"> CRITICAL {len(crit)} 项 / WARNING {len(warn)} 项", ""]

    # ---- 趋势 ----
    lines.append("## 趋势（最近 5 次）")
    lines.append("")
    lines.append("| 日期 | CRITICAL | WARNING |")
    lines.append("|------|----------|---------|")
    for rec in history[-5:]:
        lines.append(f"| {rec['date']} | {rec['critical']} | {rec['warning']} |")
    lines.append("")

    # ---- 按模块分组的汇总 ----
    lines.append("## 按模块汇总")
    lines.append("")
    lines.append("| 模块 | CRITICAL | WARNING |")
    lines.append("|------|----------|---------|")
    for mod in sorted(modules):
        mc = sum(1 for x in crit if x[2] == mod)
        mw = sum(1 for x in warn if x[2] == mod)
        lines.append(f"| {mod} | {mc} | {mw} |")
    lines.append("")

    for level, group in (("🔴 CRITICAL（违反即回滚）", crit), ("🟡 WARNING（建议修复）", warn)):
        lines.append(f"## {level}")
        lines.append("")
        if not group:
            lines.append("（无）")
            lines.append("")
            continue
        for mod in sorted(modules):
            items = [x for x in group if x[2] == mod]
            if not items:
                continue
            lines.append(f"### 模块 `{mod}`")
            lines.append("")
            for lv, rule, _m, f, detail in items:
                lines.append(f"- `[{rule}]` **{f}** — {detail}")
            lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"CRITICAL={len(crit)} WARNING={len(warn)}")
    for lv, rule, mod, f, detail in findings:
        print(f"[{lv}][{rule}][{mod}] {f} — {detail}")
    print(f"report={REPORT}")
    print(f"history={HISTORY}")
    sys.exit(1 if crit else 0)


if __name__ == "__main__":
    main()
