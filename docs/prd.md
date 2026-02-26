1. 核心技术栈建议
- 前端: React 或 Vue.js（用于复杂的模版编辑和数据报表）。
- 后端: Node.js (NestJS) 或 Python (FastAPI) —— 异步处理能力强。
- 数据库: PostgreSQL（存储结构化数据）+ Redis（任务队列与缓存）。
- 邮件发送: 基于gmail oauth

---
3. 功能模块逻辑拆解
A. 数据管理与导入
- 批量导入: 支持 CSV/Excel 上传。后端需要一个 Validation 管道，检查邮箱格式、去重，并对无效邮箱进行初步过滤。
- 变量替换: 模版引擎（如 Handlebars）是核心。你需要将用户定义的变量（如 {{first_name}}）与导入的数据进行动态映射。
B. 自动化序列 (The Sequence Engine)
这是最复杂的部分。你需要一个 状态机 来管理每个候选人的进度：
1. Step 1: 发送初始邮件。
2. Wait: 设置等待时间（如 3 天）。
3. Condition: 检查是否已回复。
4. Step 2: 如果未回复，自动触发 Follow-up。
技术关键点: 使用 Redis + BullMQ（Node.js）或 Celery（Python）来处理这种延时任务，而不是靠简单的 setTimeout。
C. 追踪系统 (Tracking)
- 打开率: 在邮件末尾注入一个 1x1 像素的透明 GIF。当图片被加载时，请求会打到你的后端接口，记录该邮件 ID 的打开事件。
- 点击率: 将邮件中的链接替换为你的 中转链接（Tracking URL），记录后重定向到目标地址。
- 回复率: 需要通过 IMAP 轮询 或 Webhook 监听用户的收件箱。如果检测到来自特定地址的回信，则停止后续的 Follow-up 序列。

---
4. 数据库表结构设计（关键表）
暂时无法在飞书文档外展示此内容

---
5. 开发路线图建议
1. MVP 阶段: 先做简单的 SMTP 绑定和单次批量发送，不带自动化序列。
2. 进阶阶段: 引入任务队列，实现 Follow-up 逻辑。
3. 完善阶段: 增加 Dashboard 数据看板，利用 Echarts 展示打开率/回复率曲线。

---
温馨提示: 批量发送邮件最头疼的是 垃圾邮件过滤（Spam Filters）。在开发时，你必须考虑 SPF、DKIM、DMARC 协议的验证，以及发送速率限制（Rate Limiting），否则邮件很快就会进垃圾桶。


优化后的用户旅程
1. 创建 Campaign：起个名字。
2. 设置 Sequence (序列)：（建议前置） 先决定发什么。
  - Step 1: 初始邮件 + 选择/编辑模版。
  - Step 2: 设置 Follow-up 间隔 + 模版。
  - 理由：先定好“戏本”，再拉“观众”入场，逻辑更顺。
3. 导入/筛选 Leads (收件人)：
  - 从 CSV 导入新名单。
  - 或者从系统的 Global Database 里勾选已有的联系人。
4. 变量映射与检查 (Review)：
  - 这是最关键的一步！系统展示“第一封邮件预览”，用户可以点击“下一个”，肉眼确认 {{first_name}} 等变量是否替换正确。
5. 发送策略 (Schedule)：
  - 选择发件邮箱账号。
  - 设置发信频率（如每 5 分钟一封）和工作时间窗。
6. 点击 Launch (启动)。

在数据库逻辑里最好加上这两个逻辑：
5.1 自动排除 (Global Unsubscribe / Blocklist)
在导入 CSV 关联到 Campaign 时，后端需要跑一个过滤逻辑： IF email IN (Global_Blacklist OR Replied_In_Other_Campaigns) THEN Skip_Import
避免把邮件发给已经投诉过你的客户，或者正在另一个活动里跟你聊天的客户。
5.2 占位符默认值 (Fallback Values)
如果用户的 CSV 里某一行缺了 first_name，邮件会变成 "Hi , I..."（多了一个空格）。
- 解决方案：在模版设置里允许定义默认值，如 {{first_name | there}}。如果名字为空，自动渲染为 "Hi there"。
