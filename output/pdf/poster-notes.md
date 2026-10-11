# PANDA Lab 海报交付说明

当前交付为英文版：海报正文、标题、图片说明、页脚、HTML 按钮和无障碍文本均使用英文，保留原有 A2 竖版设计及官方机构标识。

- `panda-lab-poster-A2.pdf`：单页 A2 竖版，420 × 594 mm。文字为可选择的 PDF 文本，保留论文、导师主页和网站链接。
- `panda-lab-poster.html`：独立、可离线打开的 HTML，图片、字体、二维码均已内嵌。
- `panda-lab-poster-preview.png`：从最终 PDF 渲染的预览图。

采用深森林绿、暖白、青柠绿及少量赤陶色。主要画面来自网站的真实实验演示视频；没有生成或虚构实验图片。导师照片沿用网站原图。

## 内容与出处

核对日期：2026-10-07。

| 内容 | 来源 |
| --- | --- |
| PANDA Lab 名称、英文全称与研究介绍 | 仓库 `index.html`、`join.html`；[课题组网站](https://panda-lab-hku.github.io/) |
| Jia Pan 姓名、Associate Professor 职称、研究方向、邮箱 | 仓库 `people.html`；[港大导师主页](https://ai.hku.hk/index.php/people/academic-staff/jpan) |
| 计算与数据科学学院、人工智能与数据科学系 | [港大学院网站](https://cds.hku.hk/)、导师主页页首机构标识 |
| 官方学院与系标识 | [港大网站 PNG](https://ai.hku.hk/images/hku-cds-ai-mono.png)，保存为 `assets/hku-ai-logo.png`；版式中等比展示为白色 |
| 导师照片 | 仓库 `people/photo/jpan_full.jpg` |
| RAPID 主视觉 | 仓库 `assets/rapid.mp4`，7.5 秒；提取真实帧，使用渐变与版式融合 |
| ALOHA 双臂操作 | 仓库 `assets/aloha.mp4`，9.0 秒 |
| GauSS-MI 三维重建 | 仓库 `assets/gausmi.mp4`，14.5 秒；裁去原视频文字边缘 |
| SoftMimic 柔性物体操作 | 仓库 `assets/softmimic.mp4`，3.7 秒；使用左侧机器人实验画面 |
| UR、Franka、ALOHA、G1、LimX Oli、Tron 平台清单 | 本次用户明确提供；画面字幕按项目名标注，不将未核实的机器人型号配到图片上 |

## 四篇代表论文

从仓库 `publications/scholar.json` 选出，以机器人研究相关性和期刊覆盖为主。作者栏为海报用简写，完整名单见论文链接。

1. Y. Yan, A. Zermane, J. Pan, A. Kheddar. **A soft skin with self-decoupled three-axis force-sensing taxels.** *Nature Machine Intelligence* 6, 1284-1295 (2024). [DOI](https://doi.org/10.1038/s42256-024-00904-9)。标题、期刊、年份经 Crossref 核对。
2. S. Lin et al. **Embodied neuromorphic synergy for lighting-robust machine vision to see in extreme bright.** *Nature Communications* 15, 10781 (2024). [DOI](https://doi.org/10.1038/s41467-024-54789-8)。标题、期刊、年份、作者经 Crossref 与导师主页核对。
3. Y. Zhang et al. **BIM-Loc: BIM-integrated discrepancy-aware LiDAR-based indoor localization.** *The International Journal of Robotics Research* (2026). [DOI](https://doi.org/10.1177/02783649261462593)。标题、作者、年份经 Crossref 与导师主页核对。
4. R. Han et al. **NeuPAN: Direct Point Robot Navigation with End-to-End Model-Based Learning.** *IEEE Transactions on Robotics* 41, 2804-2824 (2025). [论文](https://ieeexplore.ieee.org/document/10938329/)。依据仓库论文记录与导师主页。

## 编辑与导出

推荐编辑仓库 `scripts/poster_template.html` 后运行：

```powershell
python scripts/build_lab_poster.py
```

如果直接修改已交付的独立 HTML，可运行以下命令保留这些修改并重新导出：

```powershell
python scripts/build_lab_poster.py --export-only
```

也可在浏览器中打开 HTML，点击“打印 / 另存为 PDF”。设置为 A2 竖版、无页边距、启用背景图形、关闭页眉页脚、100% 缩放。现成 PDF 已包含背景并规范到精确 A2 尺寸。

字体使用 Noto Sans SC 与 Noto Serif SC 的子集，按 [SIL Open Font License](https://openfontlicense.org/) 发布；生成时读取本机安装字体，交付 HTML 内嵌子集，查看文件不依赖字体安装。

重新渲染 PDF 预览：

```powershell
pdftoppm -scale-to 2800 -singlefile -png output/pdf/panda-lab-poster-A2.pdf output/pdf/panda-lab-poster-preview
```
