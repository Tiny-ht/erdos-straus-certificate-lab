# 参考资料

以下是本项目背景与核验方法的公开来源。它们不为本项目的具体代码运行结果背书；实现证据应通过本仓库的固定提交、测试和公开 CI 记录检查。

## Erdős–Straus 方程

Spiridon Mihnea 与 Dumitru C. Bogdan，*Further verification and empirical evidence for the Erdős–Straus conjecture*，2025 年预印本。

- [arXiv 摘要与版本信息](https://arxiv.org/abs/2509.00128)
- [第一版全文](https://arxiv.org/html/2509.00128v1)

相关内容包括素数归约、同余过滤和有限范围计算。论文报告的有限验证范围不等于证明全部正整数情形。本项目的通用有序搜索边界在 [mathematics.md](mathematics.md) 中单独推导，不依赖经验性的分母截断。

## Lean 证明验证

- [Lean 官方：Validating a Lean Proof](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
- [Lean 4 官方源码](https://github.com/leanprover/lean4)

官方文档区分“形式化声明的证明有效”与“声明是否准确表达预期问题”，并介绍公理依赖检查及独立重放。`latest` 文档会随版本变化；实际构建应以仓库固定的工具链和构建记录为准。

Lean 合约、Python 检查器和完整形式化证明属于不同层次。存在一个 `.lean` 文件不表示它已经编译；局部合约编译通过也不表示有限化、搜索完备性或总猜想已经被证明。
