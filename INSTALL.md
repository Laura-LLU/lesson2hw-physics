# 安装“课后有题”

最简单：把项目链接或通用技能ZIP交给Agent，复制首页安装提示词，让它安装。老师无需执行下面的开发命令。

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

下载Release中的lesson2hw-physics-0.5.2-workbuddy.zip，使用当前客户端的本地技能导入功能安装。该包适配展示字段，题库和运行代码与通用包一致。核对技能可见后实际调用一次；尚无本项目在该客户端的独立验收记录。

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
