# Lesson2HW Physics｜课后有题

**上传板书、PPT或PDF课件，或说一句要求，生成贴合课堂的物理作业。**

面向Codex、Claude Code、WorkBuddy等AI Agent的开源技能。老师无需自建题库、配置Python或填写本项目API Key；Agent使用内置题库索引，筛选已教范围内的题目，生成独立的学生卷和答案卷，供老师复核。

**[下载通用技能包](https://github.com/Laura-LLU/lesson2hw-physics/releases/download/v0.5.1/lesson2hw-physics-0.5.1-agent-skill.zip) · [下载WorkBuddy导入包](https://github.com/Laura-LLU/lesson2hw-physics/releases/download/v0.5.1/lesson2hw-physics-0.5.1-workbuddy.zip) · [版本与校验文件](https://github.com/Laura-LLU/lesson2hw-physics/releases/tag/v0.5.1)**

当前为 **v0.5.1 Early Preview**。格式和本地出卷已经检查，各Agent客户端的真实安装、板书/PPT理解与课堂效果尚未逐一验收。

## 最简单的安装方式

把下面这段话连同本项目链接发给你的Agent，让它代为安装：

```text
请从 https://github.com/Laura-LLU/lesson2hw-physics 安装“课后有题”物理技能。
先阅读仓库README.md、INSTALL.md，以及skill/lesson2hw-physics/SKILL.md。
按当前Agent的真实技能机制安装完整lesson2hw-physics目录，检查能否识别。
默认使用内置9702/0625题库；不要让我找题库、填路径或配API Key。
首次需要联网，由你自动准备独立环境和题目/答案缓存。
不要覆盖我已有的技能改动或作业。必须本人确认的权限请说明具体动作。
课程和已教范围明确后，生成学生卷、答案卷并检查全部页面。
```

也可以下载上方ZIP，交给Agent或使用宿主提供的导入功能。GitHub访问受限时可由他人转交完整技能ZIP；首次获取未缓存题目及准备环境仍需要相应网络访问。

**无需购买培训、加群或注册作者服务才能使用本技能。** Agent本身的订阅、模型费用和权限按所用平台设置。

## 老师怎么用

- **板书**：“这是今天的板书。按已教内容给9702 AS出一份20分钟作业，排除板书例题。”
- **PPT**：“根据这份0625 Extended课件第5–12页，出6道选择题和2道结构题，不考能量。”
- **PDF课件**：“只按前8页已经讲过的内容选题，保留图像题，给我学生卷和答案卷。”
- **一句话**：“9702 A2圆周运动，3道中等结构题，不考引力。”

老师只需提供材料或要求，并复核输出。整份课件不等于全部已讲；必要时Agent会确认范围。PPT图表/公式能否完整读取取决于宿主的文档和渲染能力，详见[材料读取说明](skill/lesson2hw-physics/references/lesson-inputs.md)。无法读取时会说明并请求可读版本，不猜测课件内容。

## 已有题库，首次无需自己建库

| 课程 | 内置索引 | 当前材料范围 |
| --- | ---: | --- |
| Cambridge AS & A Level Physics 9702 | 4,330题 | AS Paper1/2、A2 Paper4、实验Paper3/5 |
| Cambridge IGCSE Physics 0625 | 2,256题 | Extended Paper2/4；暂未内置Core和实验材料 |

完整分类索引随技能安装，共 **6,586题**。题目和答案图片从作者现有[公开题库网站](https://lauraphysics.com)按需校验并缓存，包内不含整套原卷或题图。首次使用需要联网；已缓存素材可复用，未缓存素材不能离线取得。网站可用性属于运行依赖。

教学规则参考9702（2025–2027）与0625（2026–2028）；其他课程、年份和题型不冒充已支持。索引标签只用于筛候选，Agent必须看完整题答再决定是否匹配教学边界。

## 可以装在哪些Agent里

| Agent | 推荐方式 |
| --- | --- |
| Codex | 让它从本仓库安装skill/lesson2hw-physics；用$lesson2hw-physics或自然语言调用 |
| Claude Code | 安装到个人或项目技能目录；用/lesson2hw-physics或自然语言调用 |
| WorkBuddy | 下载workbuddy.zip，通过当前客户端的技能导入功能安装 |
| 其他Agent | 加载标准SKILL.md及完整资源；不支持自动发现时，可明确读取SKILL.md执行本次任务 |

Agent需要文件读写、命令执行、联网取题、完整图像阅读和PDF页面检查能力。仅有聊天或附件上传功能并不等于具备全部能力；Claude Code与Claude网页聊天/Cowork/云端会话也不能直接等同。具体安装、识别与能力检查见[INSTALL.md](INSTALL.md)。

## 安装包里有什么

- 通用SKILL.md，板书/课件/文字理解与教学边界、分课程选题和逐页复核规则。
- 两课程索引、来源、Topic、难度、分值及题答材料校验标记。
- Mac/Linux与Windows运行入口，自动准备独立Python环境、按需缓存及去重记录。
- 学生卷、答案卷、选题记录的本地导出，以及PDF渲染检查工具。
- 高级自有题库接入；普通老师不需要执行建库步骤。

默认工作文件在当前用户~/codex/lesson2hw-physics，首次准备不修改系统Python或shell配置。更换Agent后同一系统用户可复用该目录；不同班级可让Agent设置独立工作目录。

## 验证状态

已完成13项本地单元检查、通用Skill元数据检查、ZIP完整性和跨位置索引初始化。前身版本已在Mac空白工作目录自动准备环境，并分别用两门课程真实题答生成和查看作业/答案。本版本已从通用技能ZIP换目录初始化两门题库，并各生成和检查一套真实学生卷/答案卷。

尚未完成：各Agent客户端逐一实装、另一台Mac/Windows实机、真实教师PPT/板书理解系统评测和课堂效果。不能把代码测试通过当作AI选题永远正确。详见[测试状态](docs/测试状态.md)。

## 开源与参与

代码及原创规则采用[MIT许可证](LICENSE)，允许使用、修改和商用，保留版权与许可声明。第三方考试材料保留其原有权利与来源条件，不因本项目而成为MIT材料。本项目独立开发，与Cambridge International无隶属或背书关系。

培训、题库适配和学校实施服务可独立开展，免费技能不以购买这些服务为使用前提。[反馈问题](https://github.com/Laura-LLU/lesson2hw-physics/issues/new)时请提供Agent名称、系统、课程及脱敏步骤，不公开学生答卷或凭据。

开发：python -m unittest discover -s tests -v；打包：python tools/package_skill.py --output <本机输出目录>/lesson2hw-physics-agent-skill.zip，WorkBuddy包额外加--platform workbuddy。依赖见requirements.txt，输入课件与题库原素材只读。

---

**English:** Lesson2HW Physics turns board photos, lesson slides, PDF courseware, or a short request into curriculum-aligned physics homework and a separate answer PDF through a capable AI agent. It bundles metadata for 4,330 Cambridge 9702 and 2,256 Cambridge 0625 questions; paired images are fetched on demand. Standard Agent Skill core, optional WorkBuddy packaging, MIT code. Early preview: host-specific installation and lesson-understanding quality still require validation.
