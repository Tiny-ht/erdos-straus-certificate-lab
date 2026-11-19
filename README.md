# Erdős–Straus Certificate Lab

[![CI](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/workflows/ci.yml)

一个围绕 Erdős–Straus 方程构建的**有限整数搜索与证书核验研究原型**。项目把候选搜索、带作用域的排除证书、独立检查和形式化合约分开，便于复现实验，并为后续 agent 研究提供明确的验收接口。

$$
\frac4n=\frac1x+\frac1y+\frac1z,
\qquad n\ge2,\quad x,y,z\in\mathbb Z_{>0}.
$$

本项目没有证明或否定 Erdős–Straus 猜想，也没有部署持续运行的 LLM 调度器。有限测试、Python 检查器和 Lean 合约具有不同的证明范围，下面逐项说明。

## 已实现的内容

- 由严格数学边界确定的有序分母搜索，全部使用精确整数运算。
- 正见证、固定最小分母分支排除、完整搜索穷尽与预算中止的不同结果类型。
- 绑定输入、分支与版本的证书检查；重新计算边界并检查准确覆盖。
- 严格 JSON 读写，以及遗漏、重复、错误余数、类型错误和跨作用域复用等测试。
- 独立的约分因子枚举，用于交叉检查整数区间枚举。
- 可复现的样例证书与检查报告。
- Lean 合约及其独立 CI 检查配置。

Python 核验已在 $2\le n\le80$ 的 **2,558 个分支**上与因子枚举交叉检查，结果一致。这是一个有界测试集，不表示一般完备性已经由 Lean 证明。

## 快速开始

需要 **Python 3.10 或更新版本**。运行时不依赖第三方 Python 包；可以直接从源码执行。

```bash
git clone https://github.com/Tiny-ht/erdos-straus-certificate-lab.git
cd erdos-straus-certificate-lab

PYTHONPATH=src python -m unittest discover -s tests -v
```

### 生成并验证一个分支排除证书

```bash
PYTHONPATH=src python -m erdos_straus branch 5 3 --output examples/no_x_5_3.json
PYTHONPATH=src python -m erdos_straus verify examples/no_x_5_3.json --n 5 --x 3
```

这个例子关闭的是 $n=5$ 且最小分母 $x=3$ 的有序分支。完整候选只有 $y=3,4$，对应的非整除余数分别为 3 和 8。

它不否定输入 $n=5$，因为另一个分支有解：

$$
\frac45=\frac12+\frac14+\frac1{20}.
$$

```bash
PYTHONPATH=src python -m erdos_straus search 5 --output examples/witness_5.json
PYTHONPATH=src python -m erdos_straus verify examples/witness_5.json --n 5 --x 2
```

### 预算中止必须保留为 UNKNOWN

```bash
PYTHONPATH=src python -m erdos_straus search 5 --max-checks 0
```

这个命令预期返回 `UNKNOWN`，退出码为 `3`。它没有完成搜索，因此不能产生输入无解的结论。`max-checks` 限制搜索器进行的候选检查次数，不是 CPU 时间或内存上限；证书验收可能重复计算。

### 安装为命令行工具

也可以在虚拟环境内安装本项目：

```bash
python -m pip install .
es-certs branch 5 3 --output examples/no_x_5_3.json
es-certs verify examples/no_x_5_3.json --n 5 --x 3
```

## 结果类型与剪枝权限

| 类型 | 精确含义 | 可执行的动作 |
|---|---|---|
| `witness` | 给定输入有一个通过整数等式检查的有序解 | 完成该输入的存在性任务 |
| `no_x` | 给定 $n,x$ 的全部有序候选都已排除 | 仅关闭这个固定最小分母分支 |
| `exhausted` | 全部合法 $x$ 分支均由完整负证书覆盖 | 进入根节点排除的独立复核；不得省略完备性义务 |
| `unknown` | 预算耗尽等原因导致搜索未完成 | 保留未完成节点，不能记为无解 |

无效证书、输入错误或程序异常应被拒绝或报告为错误，不能被转成数学否定。一个具体三元组失败、一个分支无解和一个输入无解是三个不同命题。

完整穷尽若被解释为 $\neg ES(n)$，需要一并验证排序、有限边界和整除归约的完备性，以及检查器实现的正确性。本项目没有产生任何 Erdős–Straus 反例。

## 数学核心

对有序解 $x\le y\le z$，完整范围是

$$
\left\lfloor n/4\right\rfloor+1\le x\le\left\lfloor3n/4\right\rfloor.
$$

固定 $x$，令 $a=4x-n$、$b=nx$，则

$$
\max\left(x,\left\lfloor b/a\right\rfloor+1\right)
\le y\le\left\lfloor2b/a\right\rfloor.
$$

对这个范围内的 $y$，唯一可能的第三分母满足

$$
(ay-b)z=by.
$$

因此可以用精确整除或非零余数给出叶节点证据。完整推导、作用域合并条件，以及因子法中第二个同余何时可以省略，见 [数学定义与剪枝边界](docs/mathematics.md)。

## 复现证据

重新生成样例和确定性检查报告：

```bash
python scripts/reproduce.py
```

验证当前提交中的样例和报告是否与重新计算一致：

```bash
python scripts/reproduce.py --check
```

主要证据文件：

- [固定分支排除证书](examples/no_x_5_3.json)
- [输入 5 的正见证](examples/witness_5.json)
- [可复现检查报告](evidence/reproduction.json)
- [本地 Python 测试记录](evidence/python-tests.txt)
- [公开 CI 的固定提交与运行记录](evidence/ci.md)

这些文件是可重复计算的本地证据，不是独立第三方认证。公开的 [GitHub Actions 工作流](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/workflows/ci.yml) 在实际运行后提供对应提交的外部执行日志。核验时应同时记录 **commit SHA 和具体 workflow run 链接**，避免把不同版本的代码和结果混在一起。

## 验证状态与 Lean 边界

| 层次 | 当前范围 |
|---|---|
| Python 实现 | 本地执行过整数核验、证书篡改测试与 2,558 个分支的交叉检查 |
| Python CI | Python 3.10、3.12、3.13 均已在[公开运行记录](evidence/ci.md)中通过 |
| Lean 合约 | Lean 4.19.0 已在[公开运行记录](evidence/ci.md)中完成构建及公理依赖输出；初始本地环境未安装 Lean |
| 完整搜索的形式化正确性 | 尚未完成 |
| 常驻 LLM／多 agent 调度 | 尚未接入或部署 |
| 总猜想 | 本项目未解决 |

即使 Lean 合约通过编译，也只说明所提供的合约及局部定理通过检查；它不自动证明 Python 搜索器、完整有限化归约或全猜想。具体形式化范围见 [Lean 说明](lean/README.md)。顶部 badge 显示工作流状态，不预先保证任何一次运行成功。

## 项目导航

| 路径 | 内容 |
|---|---|
| [src/erdos_straus](src/erdos_straus/) | 搜索、检查器、JSON 证书、参考枚举和 CLI |
| [tests](tests/) | 数学边界、篡改、类型、预算及交叉检查测试 |
| [scripts/reproduce.py](scripts/reproduce.py) | 样例与确定性证据复现 |
| [docs/mathematics.md](docs/mathematics.md) | 数学归约和剪枝边界 |
| [docs/agent-design.md](docs/agent-design.md) | Agent 角色、模板量词、反例驱动搜索和扩展计划 |
| [docs/references.md](docs/references.md) | 公开论文与 Lean 官方资料 |
| [lean](lean/) | 形式化合约及工具链配置 |
| [examples](examples/) / [evidence](evidence/) | 具体证书与运行证据 |

## 后续研究

优先事项是形式化排序、完整边界与整除等价；随后可以扩展精确公式语法、模板反例证书和同余覆盖账本。LLM 可以作为候选提出者接入，但验收接口仍应独立检查证书与覆盖关系。详细路线见 [agent-design.md](docs/agent-design.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。
