# 📦 Render部署指南

## 方式1：从GitHub部署（推荐）⭐

### 步骤1：创建GitHub仓库

```bash
# 在GitHub上创建新仓库: email-tracker

# 在本地
cd D:\dev\vibecode\email-pitch-tool\tracker-render
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/email-tracker.git
git branch -M main
git push -u origin main
```

### 步骤2：在Render创建服务

1. 访问 https://render.com/
2. 点击 "New +" → "Web Service"
3. 连接GitHub仓库 `email-tracker`
4. 配置：
   - **Name**: `email-tracker`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn tracker:app`
   - **Instance Type**: `Free`

5. 点击 "Create Web Service"

### 步骤3：创建 PostgreSQL 数据库（重要！）

Render 的 Disk 不再免费，改用免费的 PostgreSQL：

1. 在 Render Dashboard 点击 "New +"
2. 选择 "PostgreSQL"
3. 配置：
   - **Name**: `email-tracker-db`
   - **Database**: `tracker`
   - **User**: 自动生成
   - **Region**: 选择与 Web Service 相同的区域
   - **Plan**: Free（90天后过期，但可以重建）

4. 创建后，复制 "Internal Database URL"

### 步骤4：连接数据库到 Web Service

1. 回到你的 Web Service 页面
2. 点击 "Environment"
3. 添加环境变量：
   - **Key**: `DATABASE_URL`
   - **Value**: 粘贴刚才复制的 Internal Database URL

4. 保存后会自动重新部署

### 步骤5：测试服务

```bash
# 替换为你的Render URL
curl https://email-tracker.onrender.com/health

# 应该返回
{"status":"ok"}

# 查看服务状态（应该显示 "database": "PostgreSQL"）
curl https://email-tracker.onrender.com/
```

---

## 方式2：直接从本地目录部署

如果不想创建单独的GitHub仓库：

### 选项A：添加到现有仓库

```bash
# 在主项目中
cd D:\dev\vibecode\email-pitch-tool
git add tracker-render/
git commit -m "Add tracker service"
git push

# 在Render中
# Root Directory: tracker-render
```

### 选项B：使用Render CLI

```bash
npm i -g @render/cli

cd tracker-render
render deploy
```

---

## 配置完成后

### 获取服务URL

在Render Dashboard中找到：
```
https://your-app-name.onrender.com
```

### 配置本地应用

```bash
# Windows
set TRACKER_URL=https://your-app-name.onrender.com

# 或创建 .env 文件
echo TRACKER_URL=https://your-app-name.onrender.com >> .env
```

---

## 验证部署

### 1. 检查服务状态

```bash
curl https://your-app.onrender.com/
```

应该看到：
```json
{
  "service": "Email Tracker V2",
  "status": "running",
  "total_opens": 0,
  "total_clicks": 0,
  "unsynced_opens": 0
}
```

### 2. 测试追踪

```bash
# 浏览器访问（模拟邮件打开）
https://your-app.onrender.com/open?uid=999

# 查看统计
curl https://your-app.onrender.com/api/stats
```

应该看到 `total_opens: 1`

---

## 🎉 完成！

你的追踪服务已经部署好了，记下URL：

```
https://your-app-name.onrender.com
```

下一步：配置本地应用使用此追踪服务
