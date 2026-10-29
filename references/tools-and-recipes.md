# 建模工具与可执行做法

所有示例坐标按毫米解释。STL 本身不记录单位；导入切片器时必须确认比例。先确定用途、关键尺寸、连接方式、打印方向与材料，再选工具。下面的试配值是演示假设，不代表任何实物的推荐间隙。

## 选择与准备

检查器依赖要求 **Python 3.10及以上**；先用 `python --version` 核对。若系统Python过旧，选择已安装的新版本再建环境。CadQuery等建模工具还需满足各自版本的安装要求。

先运行 `python --version`，并确认命令指向你准备使用的Python。用 `python -c "import shutil; print({x: shutil.which(x) for x in ['openscad', 'blender', 'bambu-studio', 'prusa-slicer']})"` 探测CLI；图形应用的实际可执行文件也可能在应用包内。找到现有可用CAD环境时直接用其Python绝对路径。

没有现成环境时可在项目内创建，避免影响其他项目：

```sh
python -m venv .venv
# macOS / Linux:
.venv/bin/python -m pip install cadquery trimesh numpy matplotlib
# Windows使用 .venv\Scripts\python.exe 替代上面的Python路径。
```

下文的 `python` 均指选定环境的解释器。只有执行对应方法才安装其依赖；记录本次实际版本。此Skill的 `requirements.txt` 仅列检查器依赖，生成CAD和画图按所用方法另装。

- **CadQuery**：尺寸精确的支架、接头、外壳，适合参数化和输出可继续编辑的 STEP。`python -m pip install cadquery`；先用 `python -c "import cadquery; print(cadquery.__version__)"` 确认环境。示例使用 CadQuery 2.8 系列 API。
- **OpenSCAD**：用代码组合基本体、重复结构和布尔运算；运行 `openscad --version` 与 `openscad --help` 查看安装和版本支持的选项。
- **Blender**：有机形状、自由曲面、雕刻和网格编辑；先运行 `blender --version`、`blender --help`，也可用图形界面操作。
- **trimesh**：读取和检查三角网格，不替代对模型结构和切片结果的判断。进入此 Skill 目录运行 `python -m pip install -r requirements.txt`。

## CadQuery：试配环

保存为 `ring.py` 并运行 `python ring.py`，会在当前目录输出 `ring.stl` 和 `ring.step`。外径、孔径、间隙、厚度均可修改；量取实物并做小样验证配合。通过两个圆拉伸生成环，用布尔减法切槽，再导出 STL 和 STEP，并重读 STEP 检查实体数：

```python
import cadquery as cq
from cadquery import exporters, importers

# Demonstration assumptions in millimetres; measure the real mating part first.
outer_d = 30.0
nominal_inner_d = 20.0
fit_clearance = 0.4  # added to diameter, not to each side
height = 5.0
inner_d = nominal_inner_d + fit_clearance
if not (0 < inner_d < outer_d and height > 0):
    raise ValueError('invalid ring dimensions')

# Two closed sketches extruded together create the through-hole.
ring = (cq.Workplane('XY')
        .circle(outer_d / 2)
        .circle(inner_d / 2)
        .extrude(height))
# Cut a shallow radial slot as a boolean operation; maintain the annulus.
notch = (cq.Workplane('XY')
         .center(outer_d / 2 - 0.5, 0)
         .box(1.0, 2.0, height + 2.0, centered=(True, True, False))
         .translate((0, 0, -1)))
ring = ring.cut(notch)
exporters.export(ring, 'ring.stl', tolerance=0.01, angularTolerance=0.1)
exporters.export(ring, 'ring.step')
# STEP re-read checks that an editable solid was actually written.
reloaded = importers.importStep('ring.step')
print('STEP solids:', reloaded.solids().size())
```

在 Skill 根目录执行：

```sh
python scripts/inspect_stl.py ring.stl --expect-size 30 30 5 --size-tol 0.1 --expect-bodies 1 --on-bed --output ring-report.json
```

模型放在别的目录时传实际路径。STL 是对曲面的三角近似，包围尺寸可能略小，误差应结合导出精度选择。STEP保留几何实体，不保留原Python参数和原始特征历史；改参数使用源码重建。STEP 重读只证明文件可解析和实体数量，配合尺寸仍需测量和试打。[CadQuery 导出文档](https://cadquery.readthedocs.io/en/latest/importexport.html)。

### 外壳/支架的常用操作

- 外壳常用“外实体减内实体”，让内腔切削体略超过上口，保留明确底厚；开口线槽也用切削体与侧壁真实相交。
- 在 `XY` 建立截面再 `extrude()` 是沿Z拉伸；`box(..., centered=(True, True, False))` 从Z=0向上建体。旋转或平移后，检查坐标与方向。
- `a.union(b)` 用于应为一体的结构，`a.cut(tool)` 切槽，`a.intersect(b)` 返回交集用于检查干涉；`translate((x,y,z))`、`rotate(...)` 处理位置。交集体积大于检查精度阈值时定位特征，不直接删零件。
- 圆角和倒角只选目标边；先检查边的方向和位置，再 `.fillet(radius)` / `.chamfer(size)`。不要把所有边一起倒大圆角，失败时按特征分步缩小范围。
- 用 `shape.val().BoundingBox()` 查询包围盒、`shape.val().isValid()` 检查实体、`shape.solids().size()` 数实体；多实体逐一检查。体积只用于确有实体的对象，空交集按0处理。
- 修改现有STEP先 `importers.importStep(path)`，在其实体上操作；修改现有参数脚本先定位参数和坐标。STL只是三角网格，不能从它保证恢复原始实体特征树。

具体选择器与API按本机CadQuery版本及 [官方示例](https://cadquery.readthedocs.io/en/latest/examples.html) 核对。复杂模型每加一个特征就做局部有效性检查，最后再独立检查导出文件。

### 遇到错误时怎么定位

| 现象 | 操作 |
|---|---|
| 加圆角/相减后实体失效 | 回到最后一个有效特征，单独查看目标边、相切/共面和切削体范围，再修改该特征重跑 |
| 导出后CAD包围盒出现微小变化 | 比较三角化前的尺寸和重新读入STEP的尺寸，排查三角缓存/几何容差；不直接改配合尺寸去抵消显示误差 |
| API不存在或参数不符 | 检查当前库版本和实际对象类型，再查本机签名/官方文档；不要靠捕获异常返回默认“通过” |
| 绘图出现只读数组错误 | 将传给会原地修改数组的绘图API的尺寸复制，例如 `mesh.extents.copy()` |
| 预览中文变方框 | 选择本机实际存在的中文字体，或改用可读英文；重新生成并打开图检查 |

参数误差、几何运算的数值容差、网格离散误差和实际打印配合余量分别处理；它们不能互相冒充。

## OpenSCAD：规则实体

保存 `ring.scad`：

```scad
outer_d = 30; inner_d = 20.4; height = 5; // mm, demonstration only
$fn = 120;
difference() {
  cylinder(h = height, d = outer_d);
  translate([0, 0, -0.1]) cylinder(h = height + 0.2, d = inner_d);
}
```

```sh
openscad -o ring.stl ring.scad
openscad -o ring.png --imgsize=800,600 --viewall --autocenter ring.scad
python scripts/inspect_stl.py ring.stl --expect-size 30 30 5 --expect-bodies 1
```

PNG 用于查看外观，STL 用于切片；运行 `openscad --help` 确认当前版本的图像选项和渲染环境。[OpenSCAD 命令行手册](https://files.openscad.org/documentation/manual/Using_OpenSCAD_in_a_command_line_environment.html)。

## Blender：自由曲面和网格处理

导入或建立模型后检查场景单位与对象的实际尺寸，完成造型后应用需要的修改器；进入编辑模式检查非流形边、孔洞、法线与相交。针对确认有问题的位置修复并复查，避免直接填掉设计上有意保留的开口。通过当前版本的“文件 → 导出 → STL”导出，并检查选择范围、缩放和单位，再用本 Skill 检查器复核。界面和 3D Print Toolbox 可用性随版本变化；按当前版本帮助和 [Blender 官方手册](https://docs.blender.org/manual/en/latest/) 查找对应操作。自动化脚本使用当前安装版本对应的 Python API。

## 从真实模型生成预览

没有CAD渲染器时，以下脚本可直接把一个STL绘成几何预览。装配预览应先将各零件放到实际装配位置，再分别绘制，不能用打印摆盘冒充装配。示例需要 `matplotlib`，它不属于STL检查器的必需依赖。

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

mesh = trimesh.load_mesh('ring.stl')
fig = plt.figure(figsize=(7, 5), dpi=160)
ax = fig.add_subplot(111, projection='3d')
ax.add_collection3d(Poly3DCollection(mesh.triangles,
    facecolors='#a7c7d9', edgecolors='#405666', linewidths=0.06))
lo, hi = mesh.bounds
ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), zlim=(lo[2], hi[2]),
       xlabel='X (mm)', ylabel='Y (mm)', zlabel='Z (mm)')
ax.set_box_aspect(mesh.extents.copy())
ax.view_init(elev=28, azim=-55)
fig.savefig('ring-preview.png', bbox_inches='tight')
plt.close(fig)
```

这是几何预览；壁厚、孔径、装配检查仍用数值和CAD剖面完成。绘图后实际打开PNG，确认没有被遮挡、裁切或反转。

## 网格检查与切片

```sh
python scripts/inspect_stl.py model.stl --expect-size 30 30 5 --size-tol 0.1 --expect-bodies 1 --on-bed --output report.json
```

参数为可选；尺寸检查比较 XYZ 包围盒，`--expect-bodies` 检查连通体数量。返回码 0 为通过，1 为检查失败，2 为输入或依赖错误。报告包含范围、尺寸、连通体、闭合、面方向、有符号体积、退化面及错误；负体积、未闭合、面方向不一致或退化面都会失败。检查时在内存中合并重合顶点以判断拓扑，原始 STL 不会被修改，也不自动补洞或删除部件。闭合网格仍可能有自相交、内部重叠、薄壁或不合适的配合；模型尺寸也不能代替实物测量。[trimesh 检查说明](https://trimesh.org/trimesh.base.html)。

检查器也检查每个独立外壳的体积方向，避免大零件的正体积掩盖小零件的反向。独立外壳反向会失败；负向外壳与正向外壳范围重叠时可能是合法内腔，工具返回需CAD复核，不自动翻面。它不完成一般的套层壳包含关系和自交分析。

`--on-bed` 用于打印摆放坐标，检查最低Z是否在0的容差内；不传此项时只做几何检查，允许装配坐标。对旋转后的零件用实际包围盒计算落床平移，不用总高度猜平移量。

在目标切片器查看其本机帮助、版本和具体命令行选项；选择真实的打印机、喷嘴、材料和配置后导入并重新切片，检查尺寸、摆放、支撑、层预览和预估时间。项目已有原生 3MF 时保留原文件及其对象、板、打印设置和元数据；优先在同一切片器中复制项目后修改、重新切片，避免把 STL 导回当作完整项目。最终以目标设备和材料的小样试打确认。

### Bambu Studio命令行流程

先用 `bambu-studio --help` 确认当前版本支持的参数；应用包里的可执行文件可替代命令名。以下参数以 Bambu Studio 02.08.02.61 命令行为例，配置文件名为示意，需要换成当前机器对应的真实配置：

```sh
bambu-studio --help
bambu-studio --load-settings 'machine.json;process.json' \
  --load-filaments filament.json --ensure-on-bed --arrange 1 \
  --slice 0 --export-3mf sliced.3mf body.stl lid.stl
# 重新打开最终工程并再次切片：
bambu-studio --slice 0 --export-3mf reopened.3mf sliced.3mf
```

优先使用官方预设或从本机切片器导出的完整配置；处理预设继承关系时保留必要字段，不能把只有几项参数的JSON冒充完整机器配置。原工程有手工摆放时不自动重排。正式打印前核对真实喷嘴/料位；不能通过 `--no-check` 或删除警告让验收变绿。运行前换成当前配置，并按目标材料和打印机核对生成的工程。
