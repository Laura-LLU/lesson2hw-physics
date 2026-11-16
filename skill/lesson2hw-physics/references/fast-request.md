# 快速范围与复核格式

由Agent填写，不让老师填写技术参数。所有Topic共用结构。

scope示例：
```json
{"course":"9702","level":"AS","topics":["2"],"query":"horizontal projectile vertical component velocity","include":["平抛、分运动、SUVAT"],"exclude":["空气阻力、能量、碰撞"],"exclude_terms":["collision","air resistance is not negligible"],"exclude_ids":[],"input_visually_reviewed":true,"input_sha256":["本次原文件SHA256"],"requirements":{"mixed":true,"minutes":40,"minutes_by_kind":{"mcq":20,"structured":20},"whole_questions_only":false}}
```

明确题量放`requirements.counts`，如`{"mcq":6,"structured":2}`；老师未指定题量，不把自定预估题量变成硬要求。分题型时长放minutes_by_kind；普通总时长放minutes。中文教学范围由Agent映射成英文query与实际Topic；9702 Topic1-25、0625 Topic1-6，P3/P5使用Practical标签及相应level。不自动认定整章已讲。

review沿用[原有格式](layout-and-request-checks.md)，但`input_sha256`为begin返回的原文件SHA数组；course/level/requirements必须与scope完全一致。每个ID包含scope_pass、answer_checked、already_taught=false、具体reason、题答SHA；节选还须independently_answerable=true。可能未知的前置知识列入prerequisites，未确认则排除。layout几何必须绑定对应图片SHA。

`candidates`只返回少量摘要，标签和全文排名不等于已审核；`fetch`只允许本次候选ID。两轮中仍不足则说明真实缺口，不能扩大教学范围或按更多原题无限下载。新小问几何和独立条件应保存为来源哈希绑定的配方；当前附6个已验收配方，不冒充全题库小问都已验收。


## 新Topic独立小问配方

`fast excerpt --from-id <已fetch的原题> --spec-file <JSON>`，将几何与原题哈希绑定并保存到本地，下次检索可直接复用。不同电脑可随用户允许的自有题库分享该配方；不含教师板书。用原图归一化坐标，先确认所有必要背景均包含。

```json
{"id":"原题ID-part-a-v1","retained_parts":"a","marks":3,"independently_answerable_reviewed":true,"retrieval_text":"保留部分的英文知识点/简短题意","question_source_sha256":"原题图SHA256","answer_source_sha256":"原答案图SHA256","question_boxes":[[0,0,1,0.4]],"answer_boxes":[[0,0,1,0.3]]}
```

多个不连续的保留区域可用多个box，按原文顺序排列。不能遗漏依赖的题干/图/数据，不得裁改选择题选项来凑数。创建后仍需查看实际生成的小问题答；几何配方不等于自动证明语义正确。
