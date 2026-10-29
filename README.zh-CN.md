# 可打印建模 Skill

[English](README.md) · 版本 0.1.0 · [MIT 许可证](LICENSE)

一套采用 [Agent Skills 格式](https://agentskills.io/specification) 的可移植建模工具包，包含建模方法、工具用法、装配规则和 STL 检查脚本。

适合制作外壳、支架、保护盖和试装件。Agent 读取规则后，按参数建立模型，导出文件并执行检查。技能正文使用中文，安装说明提供中英文两版。

## 包含什么

- CadQuery、OpenSCAD 的可执行方法，以及 Blender 和切片器的使用指引。
- 尺寸来源、单边间隙、连接器与线束空间、装配路径和打印方向。
- STL/STEP 导出与重读、网格检查、预览和 3MF 工程处理。
- 三个独立 CAD 示例，以及检查脚本的回归测试。

## 给 Agent 使用

下载并解压发布包，或使用本地源码目录。支持技能自动发现的 Agent 可以从其配置的技能目录加载；其他 Agent 可以直接读取文件。要真正生成模型，运行环境需要能执行本地建模工具。

在项目目录执行以下命令，安装精简的技能文件：

macOS / Linux：

```sh
mkdir -p "$HOME/.agents/skills/create-printable-models"
cp SKILL.md requirements.txt LICENSE "$HOME/.agents/skills/create-printable-models/"
cp -R references scripts "$HOME/.agents/skills/create-printable-models/"
```

目录以 Agent 的配置为准。只给 Codex 安装时，可把 `.agents/skills` 改为 `.codex/skills`。完成后按对应软件的方式刷新技能列表。

Windows PowerShell：

```powershell
$skillPath = Join-Path $HOME '.agents/skills/create-printable-models'
New-Item -ItemType Directory -Force $skillPath | Out-Null
Copy-Item SKILL.md,requirements.txt,LICENSE -Destination $skillPath
Copy-Item references,scripts -Destination $skillPath -Recurse -Force
```

不使用自动发现时，把整个工具包放进 Agent 可读取的工作区，发送：

> 请读取 `create-printable-models/SKILL.md` 及本任务相关的引用文件。制作一个 70 × 45 × 25 mm、使用 PETG 打印的可拆盖外壳，尺寸集中参数化，导出独立 STL 和 STEP，并检查导出文件。影响装配的缺失尺寸请先指出。

技能不要求特定模型供应商或 Agent API。只有文本能力时，可以提供规则与引用全文，由模型生成源码，再交给具备执行能力的工具运行。

## 准备 Python 环境

STL 检查器要求 Python 3.10 及以上，只需安装 `requirements.txt`。运行 CadQuery 示例再安装可选的 `requirements-examples.txt`；示例建议从 Python 3.12 环境开始。

macOS / Linux：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# 需要运行 CAD 示例时再装：
.venv/bin/python -m pip install -r requirements-examples.txt
```

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-examples.txt
```

下文的 `python` 表示选定环境的解释器，也可以直接复用已经安装所需包的现有环境。

## 检查 STL

```sh
python scripts/inspect_stl.py part.stl \
  --expect-size 80 60 33 --expect-bodies 1 --on-bed \
  --output report.json
```

把示例尺寸改为当前零件的预期值。坐标按毫米解释。`--on-bed` 检查最低 Z 是否在 0 附近，容差使用 `--size-tol`，默认 0.1 mm；装配坐标不需要此项。

报告包括范围、尺寸、连通体数量、闭合、面方向、体积和退化面，检查器不修改输入文件。返回码：**0** 通过，**1** 检查不符或需要 CAD 复核，**2** 输入、依赖或输出错误。反向的内嵌壳可能表示合法内腔，工具会提示 CAD 复核，不会自动修补。

## 三个完整示例

| 示例 | 展示内容 | 命令 |
|---|---|---|
| [试配环](examples/fit-ring/README.md) | 同一参数源生成三档孔径 | `python examples/fit-ring/build.py --output work/fit-ring` |
| [直角支架](examples/right-angle-bracket/README.md) | 底座、立板、加强肋联合为实体，孔保持贯通 | `python examples/right-angle-bracket/build.py --output work/bracket` |
| [可拆盖外壳](examples/enclosure/README.md) | 主壳和裙边盖、单边间隙、内部净空和走线通道 | `python examples/enclosure/build.py --output work/enclosure` |

每个示例将 STL、STEP、PNG 预览和 `checks.json` 写到指定目录，并自动调用检查器检查打印 STL。外壳 STEP 保留装配位置，STL 使用打印摆放位置。尺寸都是演示设计选择，可以在源码顶部修改。

![外壳示例](examples/enclosure/preview.png)

## 运行回归测试

只需要基础依赖：

```sh
python -m unittest discover -s tests -v
```

测试在临时目录生成夹具，覆盖二进制/ASCII STL、破洞、零件数量、尺寸错误、反向壳、内嵌壳、落床、无效输入和原文件保护。GitHub Actions 配置了 Linux、Windows 任务。

## 查找文件与参与改进

Agent 入口是 [SKILL.md](SKILL.md)，详细方法在 [references/](references/tools-and-recipes.md)，检查命令在 [scripts/](scripts/inspect_stl.py)，可运行 CAD 源码在 [examples/](examples/fit-ring/build.py)。

反馈问题时，附上最小源码或网格、工具版本、预期尺寸、执行命令与输出。修改检查器时补充对应的回归用例。特定打印机或材料的参数，保留在使用它们的示例或配置中。

## 许可证

[MIT](LICENSE)。第三方 CAD 引擎和 Python 包保留各自许可证。
