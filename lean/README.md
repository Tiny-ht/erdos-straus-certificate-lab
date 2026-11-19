# Lean 合约与算术叶节点

本目录固定使用 **Lean 4.19.0**，只依赖该发行版附带的 `Std`，不依赖 mathlib。
版本选择用于可复现构建，并不表示它是最新版本。

## 验证状态

初始编写环境没有 `lean` 或 `lake`，因此这份初始源码经过人工逻辑审阅，
**未在该环境编译**。公开 CI 的具体运行结果和 commit 才是构建状态的依据。
不要把 Python 测试通过当作 Lean 构建通过。

即使本目录构建成功，也只验证 `Contracts.lean` 中实际陈述的定理。
它没有证明 Erdős–Straus 猜想，也没有证明 Python 检查器与 Lean 的实现等价。

## 本目录包含什么

- `ESWitness`：用正整数和交叉乘法定义具体解。
- `checkWitness`、`acceptWitness`、`rejectWitness`：区分接受具体见证与拒绝具体见证。
- `PruneCertificate n B`：把否定证书的作用域绑定到输入 `n` 和分支 `B`。
- `mergePrunes`：只有在子分支覆盖父分支时，才允许合并否定证书。
- `noESOfRootClosed`：根节点的存在性完备性是显式前提，绝不隐式假定。
- `rejectFormula`：在已声明适用域内找到失败样本，只否定这个确定性公式。
- `witnessToResidual`、`residualToLinear`：用分配律和加法消去，把原式接到 `c*z=b*y`。
- `noWitnessOfNondivisible`：非整除证书可以排除固定 `(n,x,y)` 下的全部 `z`。
- 具体例子：`(5,2,4,20)` 是正见证；`(5,3,3)`、`(5,3,4)` 两个叶节点没有任何 `z`。

这里使用 `4*x=n+a` 和 `a*y=b+c` 描述差值，避免自然数减法截断到零的陷阱。
具体有限算术使用 `decide`，没有使用 `native_decide`。

## 尚未形式化的桥接义务

以下内容目前只在仓库数学说明中给出，不能标记为 Lean 已验证：

1. 任意正整数解排序后仍为解。
2. 有序解满足 `floor(n/4)+1 ≤ x ≤ floor(3n/4)`。
3. 固定合法 `x` 后，完整的 `y` 上下界。
4. 整除成功构造的 `z` 与有序解之间的完整双向对应。
5. Python/JSON 证书、有限区间枚举与上述 Lean 命题之间的正确性证明。
6. 用完整区间覆盖证明，把两个具体叶节点合成为 `FixedX 3` 的证书。

`complete : ES n → HasSolution n root` 是待提供的证明项；
它不是已经得到的定理，也不能通过新增自定义公理来填补。

## 构建

安装官方 Elan 工具链管理器后，在本目录运行：

```sh
lake build
lake env lean Contracts.lean
```

`lean-toolchain` 指定的发行版会由 Elan 选择。
第二条命令重新检查源文件，并在输出中显示各关键定理的 `#print axioms` 结果。
记录失败退出码，不能把源码存在或编辑器显示正常当作构建成功。

CI 应在 `lean/` 目录执行同样的命令，并把工作流运行链接绑定到具体 commit。
本项目没有外部 Lean 包依赖，因此无需下载 mathlib 缓存。

本目录仍然提交 `lake-manifest.json`：其 `packages` 数组为空，记录没有外部依赖，
而不是省略清单文件。使用的 `1.1.0` 清单格式、根包名和目录字段，依据
Lean 4.19.0 的 `Lake/Load/Manifest.lean` 核对。部分 CI 工具在构建前要求清单存在；
清单存在或格式正确本身不代表 Lean 源码已经构建成功。修改依赖配置后，应运行
`lake update` 并将相应清单变更一起提交。

## 官方参考

- [Lean 4.19.0 发行说明](https://lean-lang.org/doc/reference/latest/releases/v4.19.0/)
- [Lean 4.19.0 的 Lake 文档](https://lean-lang.org/doc/reference/4.19.0/Build-Tools-and-Distribution/Lake/)
- [Lean 4.19.0 的 Lake 清单格式源码](https://github.com/leanprover/lean4/blob/v4.19.0/src/lake/Lake/Load/Manifest.lean)
- [Lean 证明验证指南](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
