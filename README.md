# PANDA Lab · HKU

PANDA Lab（Physical AI and Autonomous Robotics）的课题组网站骨架。
参考提供的 LeCAR Lab 模板的多页面架构、学术排版和栏目组织，沿用原 PANDA Lab 首页的绿色配色。

People 页面已加入 Jia Pan 老师及表格中的成员资料。Publications 页面按要求收录 Jia Pan Google Scholar 中 2020 年至今的论文，按年份倒序排列。Join 页面已补充研究方向、意向登记表、PhD / MPhil 申请和奖学金官方入口。Visiting、Research Topics 等其他栏目仍待补充。当前文字标识和 `P` favicon 是临时标识，可在提供正式 Logo 后替换。

## 预览

直接用浏览器打开 `index.html`，或在项目目录运行：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

然后访问 <http://127.0.0.1:8000>。无需 npm、安装依赖或构建。

站点使用普通 HTML、CSS 和 JavaScript，可用于 GitHub Pages。发布时在仓库的 **Settings → Pages** 中选择部署分支及根目录。`.nojekyll` 保证文件作为静态资源提供。本次搭建只修改本地文件。

## 文件与栏目

| 文件 | 用途 |
| --- | --- |
| `index.html` | 实验室介绍、三列成果展示、News |
| `people.html` | Faculty、Postdocs、PhD、Master、Visiting Students、Alumni |
| `publications.html` | 2020 年至今的论文，按年份倒序组织 |
| `research.html` | 研究方向、相关项目、Research Talks |
| `join.html` | 加入实验室、合作与联系信息 |
| `blog.html` | 博客文章列表 |
| `styles.css` | 公共排版、绿色主题、响应式布局和内容组件 |
| `theme.js` | 明暗主题切换、偏好保存、手机导航 |
| `demos.js` | 首页视频播放与减少动态效果偏好的适配 |
| `assets/favicon.svg` | 临时浏览器图标 |

每页都包含静态的导航、页脚和内容，关闭 JavaScript 后仍可阅读并访问各页。导航和页脚调整时，需要同步修改六个页面。Google Fonts 用于加载 Source Serif 4 / Source Sans 3；字体无法加载时自动使用系统字体。

## 后续提供的资料

- 实验室简介、正式 Logo、所属学院/系及研究关键词。
- 导师和成员：姓名、身份、照片、个人主页及需要公开的链接。
- 论文：标题、作者、年份、会议/期刊、封面或视频、论文/代码/项目链接。
- 研究方向：标题、简介、图片或演示视频、相关论文。
- 新闻：日期、内容及可选链接。
- 招生/招聘：岗位、申请要求、方式、联系邮箱及地址。
- 博客：标题、作者、日期、正文及图片。
- 确认后的 GitHub、YouTube 等公开账号。

无需一次提供全部资料，可以按栏目逐步补充。栏目数量和成员分类也可按实际情况调整。

## 首页 Demo

首页 Research Highlights 已加入 ALOHA、GauSS-MI、LASP、RAPID、SoftMimic 五个视频。桌面三列、平板两列、手机一列，视频完整显示，不裁切画面。默认静音自动循环播放，并保留原生暂停、音量和全屏控件；访客启用系统「减少动态效果」时改为手动播放。

原视频保留在 `assets/` 中。页面使用 `assets/demos/` 内的 H.264 / AAC MP4 网页版本（最高 720p，已启用 fast start），以及同名 JPG 封面。原始 `gausmi.mp4` 为 HEVC 编码，网页使用其 H.264 版本以兼容更多浏览器。

更换原视频后，运行以下命令重新生成网页视频和封面：

```powershell
python scripts/prepare_demos.py --ffmpeg "你的 ffmpeg.exe 路径"
```

如果 FFmpeg 已加入 PATH，可省略 `--ffmpeg` 参数。新增视频时同步更新脚本中的 `DEMOS` 列表和 `index.html` 中的展示卡片。首页不显示视频标题；供屏幕阅读器使用的视频名称在对应 `video` 的 `aria-label` 中维护。

## People 数据更新

- `people/raw/`：最新收集表和 `图片/` 文件夹，已由 `.gitignore` 中的 `raw/` 规则忽略；导入过程只读，不移动或修改这些文件。
- `people/members.json`：清洗后的完整成员数据，是日常生成页面的数据源；不包含表内的提交时间、提交者字段或电话号码。
- `people/data.xlsx`：此前的 18 人收集表，保留作历史参考；只有尚无 `members.json` 时才用作初始化来源。
- `people/photo/`：成员原照片按 `GivenName_FamilyName.jpg` 规范命名复制（PNG、WebP 保留相应扩展名），图片内容不变。老师提供的原照片保留为 `jpan_full.jpg`。
- `people/portraits/`：网页使用的正方形 WebP 头像，最长 480 像素，已处理原图方向并检查裁切。
- `people/photo-filenames.json`：原文件名、新文件名、收集表单元格和原图 SHA-256 的对应记录，便于追溯。
- `scripts/build_people.py`：导入收集表、更新 People 页及头像的脚本。HTML 为静态输出，浏览网站无需 Python。

本次已导入 39 位成员：4 位 Postdocs、20 位 PhD、3 位 Master，以及 12 位 Alumni；另保留 Jia Pan 的 Faculty 卡片。

将最新 `.xlsx` 和配套的 `图片/` 放入 `people/raw/` 后，在项目目录运行：

```powershell
python scripts/build_people.py --import-raw
```

`raw` 目录应仅包含一份收集表（忽略 Excel 临时锁文件）。导入时自动统一姓名顺序、标点和主页协议，复制照片并生成 `members.json`、照片映射、头像和静态页面。原表的「是／否」决定成员进入 Alumni 还是在组类别；用户确认的修正优先于原表。已有规范照片会用本次收集照片更新。重复姓名、照片缺失或导入遗漏已有成员时会停止并提示。

日常修改 `people/members.json` 后，无需 `raw` 即可重新生成：

```powershell
python scripts/build_people.py
```

生成脚本需要 Pillow（`python -m pip install Pillow`）。收集表沿用「姓在前、名在后」格式，网页和 JSON 使用「名在前、姓在后」。中文姓名「郭骏德」映射为 Junde Guo。更换已有成员照片时可更新 `people/photo/` 中的规范文件名，再执行日常生成命令。

已有邮箱和研究方向修正保留在脚本中的 `EMAIL_OVERRIDES`、`RESEARCH_OVERRIDES`。`MEMBER_OVERRIDES` 保存用户确认的修正：Zhaole Sun 为在组 Postdoc（2026 年加入），Wentao Chen 为在读 PhD（2021 年入学），两人均清空原表误填的毕业信息；Wanli Xing 的工作单位为 Sharpa，Chen Wang 为 AgiBot。重新导入也会保留这些修正。若其他校友的离组年份早于加入年份，脚本会提示，并将网页时间显示为 `To be confirmed`，不猜测日期。需要在后续导入中保留的人工修正应同步维护到对应覆盖配置。

2026-10-11 核对剩余占位信息：[Jiaming Qi 的学校主页](https://cmee.nefu.edu.cn/info/1075/6397.htm) 列明港大博士后经历为 2023.06–2024.11，已补入离组时间 November 2024。[Lei Yang 的个人主页](https://leiyangjustin.github.io/) 列出博士后 2018–2021、Research Officer 2021–2023；经用户确认，本站采用 2021–2023 的在组时间。两项补充均保存在 `MEMBER_OVERRIDES` 中。

在组成员按类别、入学／加入年份从早到晚排列，同一年保持原表顺序。已毕业／离组的成员进入 Alumni，并展示在组时间和去向。表内有主页或邮箱时才显示对应图标；其他联系方式不自动变成网页链接。Research 的英文大小写和标点做了统一，中文条目已译为英文；空白研究方向显示 `To be added.`。

`people.html` 中 `PEOPLE DATA START` 与 `PEOPLE DATA END` 之间由脚本生成。Faculty、页面导航和页脚位于标记之外，不会被脚本覆盖。

Faculty 卡片中的 Jia Pan 姓名、Associate Professor 职称和研究方向来自[香港大学官网](https://ai.hku.hk/index.php/people/academic-staff/jpan)，邮箱使用提供的 `jpan@cs.hku.hk`。展示头像为 `people/portraits/Jia_Pan.webp`，由提供的原照片裁切生成，未放大原图。

## Publications 数据更新

论文来源为 [Jia Pan 的 Google Scholar 页面](https://scholar.google.com/citations?hl=zh-CN&user=YYT8-7kAAAAJ&view_op=list_works&sortby=pubdate)。`publications/scholar.json` 保存所选年份的标题、作者、发表信息和来源链接，并记录获取时间。页面由本地数据生成，访客浏览网站时无需请求 Google Scholar。

```powershell
# 用保存的数据重新生成页面
python scripts/build_publications.py

# 从 Scholar 更新数据后重新生成（需要网络和 beautifulsoup4）
python scripts/build_publications.py --refresh
```

缺少解析依赖时，可运行 `python -m pip install beautifulsoup4`。更新脚本仅访问正常的 Scholar 分页和论文详情页；若列表访问失败，不会用不完整列表覆盖已保存的数据。

规则：按 Scholar 的年份筛选 2020 年至当前年份，未标年份的条目不推断年份；期刊、会议和预印本按来源保留，唯一标识重复时停止导入。Scholar 列表中被省略的作者会尝试从详情页补全，其余作者保留原列表的姓名缩写。Google Scholar 链接指向来源记录；只有从详情页读到论文网址时才增加 Paper 链接。封面图、视频、代码和项目链接可在后续提供资料时补充。

`publications.html` 中 `PUBLICATIONS DATA START` 与 `PUBLICATIONS DATA END` 之间由脚本生成。后续编辑论文条目应修改 `publications/scholar.json`；使用 `--refresh` 会重新读取 Scholar 信息。

## Join 页面

招生说明和意向登记表入口参考 [Jia Pan 的 HKU 官网](https://ai.hku.hk/index.php/people/academic-staff/jpan)。按照官网说明，学生咨询优先使用表单；页面邮箱用于研究合作联系。PhD / MPhil 申请及奖学金信息链接至 [HKU 官方招生页](https://ai.hku.hk/index.php/programmes/research-based/mphil-phd-admission)，具体要求和截止时间以该页最新信息为准。意向登记不能替代正式入学申请。尚未确认的岗位和资助承诺不在页面中发布。

## 填入内容

HTML 注释标出了待替换区域。填入实际内容时，删除相应的空状态，而不是在它下面追加内容。所有资源使用相对路径。

建议后续把头像放入 `assets/people/`，研究图片放入 `assets/research/`，论文封面放入 `assets/publications/`，博客放入 `blog/<文章名>/index.html`。这些目录在有实际文件时再创建。

`styles.css` 已预留以下组件，可直接沿用：

- `.showcase` / `.showcase-item`：首页图片、视频展示。
- `.people-grid` / `.person` / `.person-name` / `.person-role` / `.person-links`：成员卡片。
- `.pub` / `.pub-media` / `.pub-title` / `.pub-authors` / `.pub-venue` / `.pub-links`：论文条目。
- `.topic`：研究方向；支持用原生 `details` 展开相关论文。
- `.alumni`：校友表格。
- `.post-preview` / `.post-meta` / `.post-body`：博客列表与文章。

例如，成员卡片的结构如下。示例仅用于说明，不会显示在站点上：

```html
<div class="people-grid">
  <article class="person">
    <img src="assets/people/member.jpg" alt="成员姓名" width="400" height="400" loading="lazy">
    <h3 class="person-name">成员姓名</h3>
    <p class="person-role">成员身份</p>
    <!-- 确认链接后再添加 .person-links -->
  </article>
</div>
```

新增博客详情页时，样式、脚本、图标及根页面链接都应使用 `../../` 前缀。保留每页唯一的 `h1`，并为图片补充准确的替代文字。
