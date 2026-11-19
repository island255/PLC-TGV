# PLC-TGV 论文复现材料

这份材料对应论文最终统计的 **998 项任务**，包括任务清单、安全要求、逐项判定和计时、消融记录、静态分析代码，以及 8 个可实际检查的正常 ST 程序。[English README](README.md)

## 复算结果

在仓库根目录运行以下两条命令。需要 Python 3.8 或更新版本，仅使用标准库，无需联网或启动 Docker。每次复算指定一个新的输出目录。

```shell
python -B tools/verify.py
python -B reproduce.py --output reproduced
```

打开 `reproduced/results_zh.md` 可阅读检测、消融及耗时结果。英文表为 `results_en.md`，逐项配对时间比等统计保存在 `summary.json`。[预期中文表](reference/results_zh.md)

| 方法 | 998 项端到端 F1 | 每项提交任务的平均耗时 |
| --- | ---: | ---: |
| PLC-TGV | 98.08% | 0.85 秒 |
| PLC-Defuser | 28.86% | 48.35 秒 |
| ESBMC-LLB | 94.56% | 5.52 秒 |

时间列来自论文实验的原始计时。重新生成表格时直接读取这些记录。

## 数据与代码

- [任务索引](data/task_index.json)包含 660、317、21 项任务，对应数据集 1、2、3。相同源码参与不同任务时保留各自编号。数据集 3 由 5 项长延迟攻击及 8 对计数结构的攻击和正常版本组成。
- [安全要求索引](data/property_index.json)关联全部 998 项任务所用的原始性质文件。按文件字节去重后共有 6 份。
- [实验记录](results/)包含每种方法各 998 条判定与计时，以及三个消融配置各 21 条记录。重放记录保留确认结果和输入序列指纹。
- [源码分析组件](analysis/README.md)提供 ST 解析、单扫描控制流图、性质依赖分析、标量执行和正常样本上的有限状态检查。组件说明列出了运行命令和适用范围。
- [PLCopen XML 静态前端](xml_frontend/inspect_plcopen.py)读取本地工程，列出程序单元、ST 语句类别和 LD 连线。模块来源记录在[文件清单](xml_frontend/module_origins.json)中。
- [数据来源](docs/DATA.md)给出基准版本及原始记录中的路径。第三方程序由上游发布。公开包收录 8 个正常程序的源码，省略可执行攻击程序及可触发攻击的输入序列。

三种方法的全量论文表可以离线复算。在全部 998 项上重新测量检测器耗时还需要原始程序和完整求解环境。详见[评测指标](docs/METRICS.md)和[许可说明](LICENSE.md)。
