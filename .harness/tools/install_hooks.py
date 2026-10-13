# -*- coding: utf-8 -*-
"""幂等安装 git pre-commit 钩子。

写入 .git/hooks/pre-commit（bash 脚本）：
    #!/bin/bash
    python .harness/tools/harness_gate.py --fast
    exit $?

幂等规则：已存在且内容相同则跳过；已存在且不同则备份为 pre-commit.bak 再写入。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".git" / "hooks" / "pre-commit"
BACKUP = HOOK.with_suffix(".bak")

CONTENT = "#!/bin/bash\npython .harness/tools/harness_gate.py --fast\nexit $?\n"


def main():
    HOOK.parent.mkdir(parents=True, exist_ok=True)
    if HOOK.exists():
        old = HOOK.read_text(encoding="utf-8")
        if old == CONTENT:
            print(f"已存在且内容相同，跳过：{HOOK}")
            sys.exit(0)
        BACKUP.write_text(old, encoding="utf-8")
        print(f"已存在但内容不同，已备份到：{BACKUP}")
    HOOK.write_text(CONTENT, encoding="utf-8")
    print(f"已写入：{HOOK}")
    sys.exit(0)


if __name__ == "__main__":
    main()
