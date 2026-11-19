# 公开 CI 核验记录

以下结果已经从 GitHub Actions 的实际运行状态与日志中核对。这一记录对应固定提交，
并不预先保证之后每个提交都成功。

- 核验提交：[4ce2e24817df6eff2887cc6928da3380c64d6865](https://github.com/Tiny-ht/erdos-straus-certificate-lab/commit/4ce2e24817df6eff2887cc6928da3380c64d6865)
- 完整运行：[Certificate checks #2](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/runs/44510167189)
- 触发方式：提交到 `main` 的 `push`。
- 总结果：`completed / success`。

| 任务 | 结果 | 可公开核验的记录 |
|---|---|---|
| Python 3.10 | success | [job 135512015281](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/runs/44510167189/job/135512015281) |
| Python 3.12 | success | [job 135512014736](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/runs/44510167189/job/135512014736) |
| Python 3.13 | success | [job 135512015065](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/runs/44510167189/job/135512015065) |
| Lean 4.19.0 contracts | success | [job 135512015206](https://github.com/Tiny-ht/erdos-straus-certificate-lab/actions/runs/44510167189/job/135512015206) |

Python 任务包括完整 unittest、确定性报告重放、带明确作用域的证书核验，以及安装后的命令行入口检查。

## 实际日志摘录

以下保留原始运行时间戳；时间为 UTC。完整日志在上表对应任务中。

Python 3.12：

```text
2026-11-19T10:56:04.4171830Z Ran 26 tests in 1.039s
2026-11-19T10:56:04.4172112Z OK
2026-11-19T10:56:04.6685230Z MATCH examples/no_x_5_3.json
2026-11-19T10:56:04.6686050Z MATCH examples/witness_5.json
2026-11-19T10:56:04.6686721Z MATCH evidence/reproduction.json
2026-11-19T10:56:04.6687430Z Cross-checked 2558 branches; exact solution sets agree.
```

Lean：

```text
2026-11-19T10:56:03.2642824Z Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)
2026-11-19T10:56:04.0177828Z ℹ [2/3] Built Contracts
2026-11-19T10:56:04.0189989Z Build completed successfully.
2026-11-19T10:56:04.4076118Z 'ErdosStraus.noESOfRootClosed' does not depend on any axioms
2026-11-19T10:56:04.4078235Z 'ErdosStraus.noWitnessOfNondivisible' depends on axioms: [propext]
2026-11-19T10:56:04.4079364Z 'ErdosStraus.fiveHasSolution' does not depend on any axioms
2026-11-19T10:56:04.4080322Z 'ErdosStraus.fiveThreeThreeClosed' depends on axioms: [propext]
2026-11-19T10:56:04.4081293Z 'ErdosStraus.fiveThreeFourClosed' depends on axioms: [propext]
```

## 如何理解这些结果

公开 CI 补上了外部可查看、可重跑的执行记录。初次运行曾因缺少 Lake 清单在编译前停止，
提交空依赖清单后才取得上面的完整成功记录；历史失败记录仍保留在 Actions 中。

这里的 Lean 构建只验证 `Contracts.lean` 实际陈述的合约和局部定理。
`noESOfRootClosed` 的根完备性仍是显式前提，完整搜索边界与 Python/JSON 对应尚未形式化。
`propext` 是日志明确列出的标准公理依赖，没有把它隐藏或当作零公理。

本次核验没有发现 Erdős–Straus 反例，也没有证明总猜想。
