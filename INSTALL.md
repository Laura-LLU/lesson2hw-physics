# 安装“课后有题”

最简单：把项目链接或通用技能ZIP交给Agent，复制首页安装提示词，让它安装。老师无需执行下面的开发命令。

## 给Agent的自动准备工作流

本流程仅在用户明确要求安装或准备题库时执行；仅粘贴链接不自动构成执行安装程序的授权。用户只需一句话，后续步骤由Agent完成。

1. 读取README与skill/lesson2hw-physics/SKILL.md。确认当前宿主能读写本机文件、执行命令、联网、查看图片/PDF；缺项就明确说明，不伪装完成。
2. 下载Release中的完整技能包或获取完整技能目录。识别宿主实际安装机制；已有同名技能先检查版本与用户改动，保护现有作业和缓存。
3. WorkBuddy优先使用其原生导入功能。当前官方对话安装仅覆盖市场技能，不把一个GitHub链接称为市场安装链接。项目级开发会话可按官方文档使用当前项目的.codebuddy/skills/lesson2hw-physics目录；这仅对相应项目生效，不宣称在所有会话全局安装。没有可用的自动导入能力时，请老师只完成“添加技能→上传技能”的一次导入。不要猜测未文档化的全局目录或修改内部数据库。
4. 从实际技能位置调用scripts/run.sh，依次执行info --course 9702与info --course 0625。入口自动准备独立Python及依赖。默认本机目录为~/codex/lesson2hw-physics；需要隔离时由Agent指定PHYSICS_HOME，不要求老师填写。两个索引应分别为4330与2256条。只初始化索引，不下载所有题目；题答在选题时按需缓存。
5. 核对持久技能是否被宿主识别；本轮显式读取SKILL.md可执行，不等于持久安装成功。只报告实际完成的状态。成功后简短回复“技能与内置题库已准备好，请上传板书、PPT或PDF课件，或直接说作业要求”。此时无需询问课程或自动出测试卷。
6. 收到课件/要求后按技能教学边界工作。课程或已讲页码不清时只询问必要信息；完整读取题答，导出学生卷与答案卷，检查所有页面并交付文件链接。题量、难度和排除项由当前教师要求决定，不固定套用安装测试的圆周运动题。

不得要求普通老师自建题库、配Python或填写本项目API Key。不要静默更改系统安全设置；遇到宿主要求本人操作的权限或导入步骤，简短交接，完成后继续。

## Codex

告诉Codex：从Laura-LLU/lesson2hw-physics仓库的skill/lesson2hw-physics安装技能。存在原生技能安装工具时优先使用；支持目录安装的版本可以把完整文件夹放在个人~/.agents/skills/或项目.agents/skills/下，实际位置以当前安装器为准。安装后在下一轮或新会话检查是否识别$lesson2hw-physics。文件复制成功不等于已经加载。

已有Codex官方skill-installer的环境可由Agent使用：

```text
install-skill-from-github.py --repo Laura-LLU/lesson2hw-physics --path skill/lesson2hw-physics
```

这是安装器脚本的参数示例，不是要求老师直接输入的全局命令；脚本实际位置由Agent定位。

## Claude Code

下载通用ZIP或读取仓库，将完整lesson2hw-physics文件夹安装到~/.claude/skills/（个人）或<项目>/.claude/skills/（项目）。必要时开启新会话，检查/lesson2hw-physics是否可用。Claude网页、Cowork或云端运行模式要另行确认技能加载、文件访问与执行能力。

## WorkBuddy

下载Release中的lesson2hw-physics-0.5.4-workbuddy.zip，使用当前客户端的本地技能导入功能安装。该包适配展示字段，题库和运行代码与通用包一致。核对技能可见后实际调用一次；尚无本项目在该客户端的独立验收记录。

## 其他Agent

完整加载skill/lesson2hw-physics/SKILL.md、scripts、references和resources。没有自动发现技能的机制时，用户可以明确指示读取SKILL.md并执行本次任务；这不等于已经持久安装。缺少执行、联网或视觉工具时应具体说明，不能伪造作业完成。

## 首次运行验收

1. Agent定位实际技能目录，确认可读写文件、执行命令、联网并查看图像/PDF。
2. Mac/Linux通过bash scripts/run.sh info --course 9702（或0625）自动准备独立环境，Windows用PowerShell执行scripts/run.ps1。
3. 看到9702 4330题或0625 2256题，再根据教师要求search、查看完整题答、export和qa。
4. 交付可打开的student.pdf和answers.pdf，说明实际数量、课程范围和待复核项。仅初始化成功不算完成出卷。

首次环境及素材下载需要网络和宿主正常授权；不需要老师自建题库、配置Python或本项目API Key。模型订阅/额度由当前Agent提供。

默认数据在~/codex/lesson2hw-physics。PHYSICS_HOME可由Agent指定独立目录。安装更新时不盲目覆盖已有技能改动；保留工作目录里的缓存、已用题记录和输出。旧试用包名physics-homework若仍安装，先辨别是否重复激活，不自动删除。

详细规则与当前官方文档来源见[跨Agent说明](skill/lesson2hw-physics/references/agent-installation.md)。
