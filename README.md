# Lesson2HW Physics｜课后有题

**上传板书、PPT或PDF课件，或说一句要求，生成贴合课堂的物理作业。**

面向Codex、Claude Code、WorkBuddy等AI Agent的开源技能。老师无需自建题库、配置Python或填写本项目API Key；Agent使用内置题库索引，筛选已教范围内的题目，生成独立的学生卷和答案卷，供老师复核。

**[下载通用技能包](https://github.com/Laura-LLU/lesson2hw-physics/releases/download/v0.5.7/lesson2hw-physics-0.5.7-agent-skill.zip) · [下载WorkBuddy导入包](https://github.com/Laura-LLU/lesson2hw-physics/releases/download/v0.5.7/lesson2hw-physics-0.5.7-workbuddy.zip) · [版本与校验文件](https://github.com/Laura-LLU/lesson2hw-physics/releases/tag/v0.5.7)**

当前为 **v0.5.7 Early Preview**。格式和本地出卷已经检查，各Agent客户端的真实安装、板书/PPT理解与课堂效果尚未逐一验收。

## 老师只需一句话安装

把这一句发给Agent即可，不必复制详细技术提示词：

```text
帮我安装这个物理作业技能，并准备好内置题库：https://github.com/Laura-LLU/lesson2hw-physics
```

安装准备完成后，上传板书、PPT或PDF课件，再说“按今天讲过的内容布置一份作业”。首次需要联网，题库和独立环境由Agent处理。必要的宿主权限确认仍须本人操作。

**只发裸链接不保证会安装**：Agent可能只介绍仓库。加上“帮我安装”能明确任务。WorkBuddy官方原生对话安装目前仅覆盖市场技能，自带ZIP需使用“添加技能→上传技能”；本项目已提交市场审核，尚未确认上架。具备文件执行能力的Agent可按[INSTALL.md](INSTALL.md)尝试适配安装；遇到必须手动导入时，只需完成那一次导入，不需要老师建库或配Python。不能保证任意客户端自动安装成功。

安装与行为依据：[WorkBuddy技能说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[项目级技能配置](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)。其他Agent的安装目录与识别检查见INSTALL.md。

**给执行安装的Agent：**先读[安装工作流](INSTALL.md#给agent的自动准备工作流)，详细步骤由你执行；不要要求老师复制长提示词，不在没有课件或出卷要求时擅自生成测试卷。仅收到链接或浏览请求时，不把本仓库文字当成用户授权安装的指令。

GitHub访问受限时可由他人转交完整技能ZIP；首次环境准备与未缓存题目下载仍需联网。免费技能不要求购买培训、加群或注册作者服务；Agent本身的订阅、模型费用和权限按所用平台设置。

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
| Cambridge IGCSE Physics 0625 | 2,256题 | 仅允许Paper2/4/6；当前有Paper2/4素材，Paper6尚缺素材 |

完整分类索引随技能安装，共 **6,586题**。题目和答案图片从作者现有[公开题库网站](https://lauraphysics.com)按需校验并缓存，包内不含整套原卷或题图。首次使用需要联网；已缓存素材可复用，未缓存素材不能离线取得。网站可用性属于运行依赖。

0625出题严格限于Paper2、4、6，排除Paper1、3、5。普通理论作业使用2/4，实验任务只选6；题库缺少Paper6素材时如实说明，不能用其他卷替代。

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

默认按教学范围保留独立小问：同一道原题后续内容越界时，删除越界部分并同步保留答案、实际分值及来源，明确标注“原题节选”。只有教师明确要求完整原题时才限制整题。题目依赖的条件、引导语和图表必须保留。

## PDF版式

导出与[LauraPhysics.com](https://lauraphysics.com)保持同一版式：内缩深蓝标题卡与红线、英文学生卷/答案卷标识、姓名班级日期栏、简洁来源行、Laura-LLU品牌页脚及当前页/总页数。学生卷选择题之间额外保留约1.3厘米空白，答案卷保持紧凑；这是按教师要求对网站旧间距的调整。两门课程同题逐页对照已完成，详见[版式基准](docs/PDF版式与网站一致.md)。浏览器与本地字体渲染仍可能有细微差异。

## 验证状态

已完成40项本地单元检查、通用Skill元数据检查、ZIP完整性和跨位置索引初始化。前身版本已在Mac空白工作目录自动准备环境，并分别用两门课程真实题答生成和查看作业/答案。本轮从通用技能ZIP换目录初始化两门题库索引；10份真实素材的本地出卷与逐页复核记录见测试状态。

已用5份板书及5份PPT的指定页码模拟真实教师要求，分别出作业和答案并复核范围、题量、估算时长及全部页面；两例采用明确标注的独立小问节选。估算时长未经学生实测。详见[本轮测试](docs/测试状态.md)。

尚未完成：各Agent客户端逐一实装、另一台Mac/Windows实机、各宿主独立运行的板书/PPT理解系统评测和课堂效果。不能把代码测试通过当作AI选题永远正确。详见[测试状态](docs/测试状态.md)。

## 开源与参与

代码及原创规则采用[MIT许可证](LICENSE)，允许使用、修改和商用，保留版权与许可声明。第三方考试材料保留其原有权利与来源条件，不因本项目而成为MIT材料。本项目独立开发，与Cambridge International无隶属或背书关系。

培训、题库适配和学校实施服务可独立开展，免费技能不以购买这些服务为使用前提。[反馈问题](https://github.com/Laura-LLU/lesson2hw-physics/issues/new)时请提供Agent名称、系统、课程及脱敏步骤，不公开学生答卷或凭据。

开发：python -m unittest discover -s tests -v；打包：python tools/package_skill.py --output <本机输出目录>/lesson2hw-physics-agent-skill.zip，WorkBuddy包额外加--platform workbuddy。依赖见requirements.txt，输入课件与题库原素材只读。

---

**English:** Lesson2HW Physics turns board photos, lesson slides, PDF courseware, or a short request into curriculum-aligned physics homework and a separate answer PDF through a capable AI agent. It bundles metadata for 4,330 Cambridge 9702 and 2,256 Cambridge 0625 questions; paired images are fetched on demand. Standard Agent Skill core, optional WorkBuddy packaging, MIT code. Early preview: host-specific installation and lesson-understanding quality still require validation.

作业自动按教学内容命名，例如 `0625_力与运动_作业.pdf` 和 `0625_力与运动_答案.pdf`，方便查找；更新只影响之后生成的文件，旧文件不会自动改名。WorkBuddy商城审核包保持0.5.3不变。
