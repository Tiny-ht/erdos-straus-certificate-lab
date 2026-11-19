# 核验证据

本目录把可重放的数学结果与一次实际终端运行记录分别保存。

- `reproduction.json`：有限交叉核验的范围、结果、篡改拒绝结果、源码 SHA-256。由 `python scripts/reproduce.py` 生成；`python scripts/reproduce.py --check` 重算并逐字节比较，不改写文件。
- `python-tests.txt`：发布准备期间实际执行 unittest 的原始输出，附执行命令和 Python 版本。耗时与版本不参与确定性比较。
- GitHub Actions 的 [`ci.yml`](../.github/workflows/ci.yml) 会在新的提交上重新运行 Python 测试、样例核验和 Lean 编译。请检查对应提交的运行状态与日志，不要只看一张静态截图或仓库首页的文字。

`reproduction.json` 不记录用户名、机器路径或环境变量。报告的源码哈希便于发现改动；任何人都能生成哈希，因此哈希本身不认证发布者身份，也不能替代重放。

这些记录证明的范围是明确列出的计算与合约。它们不说明存在常驻 agent 服务，也不证明 Erdős–Straus 猜想。
