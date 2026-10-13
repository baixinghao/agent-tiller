# -*- coding: utf-8 -*-
"""Harness 质量门禁编排器。

--fast（默认，pre-commit 用，阻断式）：
  1. 检测 git 暂存区/工作区是否有 .java 变更，
     或 ast_index.json 比任一 .java 旧 -> 先重建 AST 索引
  2. 运行 ddd_compliance_check.py；存在 CRITICAL -> 退出 1 并打印阻断信息
--full：在 fast 基础上追加 doc_freshness_scan / doc_link_check / doc_drift_scan（非阻断）

无参数默认 --fast。
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / ".harness" / "tools"
AST_INDEX = ROOT / ".harness" / "index" / "ast_index.json"


def log(msg):
    print(f"[harness-gate] {msg}")


def run(script, blocking=False):
    """运行子脚本，返回退出码。"""
    log(f">>> python .harness/tools/{script}")
    r = subprocess.run([sys.executable, str(TOOLS / script)], cwd=ROOT)
    log(f"<<< {script} exit={r.returncode}" + ("（阻断）" if blocking and r.returncode else ""))
    return r.returncode


def java_changed_in_git():
    """暂存区或工作区存在 .java 变更。"""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--", "*.java"],
                             cwd=ROOT, capture_output=True, text=True, timeout=30)
        return bool(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False


def index_stale():
    """ast_index.json 比任一 .java 旧。"""
    if not AST_INDEX.exists():
        return True
    idx_mtime = AST_INDEX.stat().st_mtime
    for d in ROOT.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        src = d / "src"
        if not src.is_dir():
            continue
        for jf in src.rglob("*.java"):
            if jf.stat().st_mtime > idx_mtime:
                return True
    return False


def main():
    full = "--full" in sys.argv

    log("模式：" + ("FULL" if full else "FAST") + f"，工作目录 {ROOT}")

    log("步骤 1/2：AST 索引新鲜度检查")
    changed = java_changed_in_git()
    stale = index_stale()
    log(f"  git .java 变更={'有' if changed else '无'}，索引过期={'是' if stale else '否'}")
    if changed or stale:
        log("  触发重建 build_ast_index.py")
        if run("build_ast_index.py", blocking=True) != 0:
            log("❌ AST 索引重建失败，门禁终止")
            sys.exit(1)
    else:
        log("  索引新鲜，跳过重建")

    log("步骤 2/2：DDD 合规检查（阻断式）")
    rc = run("ddd_compliance_check.py", blocking=True)

    if full:
        log("FULL 模式：追加文档健康检查（非阻断）")
        for script in ("doc_freshness_scan.py", "doc_link_check.py", "doc_drift_scan.py"):
            run(script)

    if rc != 0:
        log("❌ 门禁阻断：存在 CRITICAL 违规，请先修复后再提交（详见 .harness/index/COMPLIANCE_REPORT.md）")
        sys.exit(1)
    log("✅ 门禁通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
