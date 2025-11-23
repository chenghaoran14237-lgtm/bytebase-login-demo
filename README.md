# Bytebase-like Login Demo

这是一个仿 Bytebase 风格的登录页面 Demo，用来完成如下要求：

- 支持 **GitHub + Google 第三方登录**
- 使用 **Python + Supabase** 实现后端用户登录 / 管理接口
- 前端部署在 **GitHub Pages**
- 后端部署在 **PythonAnywhere**


---

## 1. 在线地址

请根据实际情况替换：

- 前端（GitHub Pages）：  
  `https://YOUR_GITHUB_USERNAME.github.io/bytebase-login-demo/`

- 后端（PythonAnywhere）：  
  `https://chenghaoran14237lgtm.pythonanywhere.com`

（访问前端页面后，通过 GitHub / Google 即可登录。）

---

## 2. 功能说明

### 登录与当前用户

- 支持：
  - GitHub OAuth 登录
  - Google OAuth 登录
- 登录成功后：
  - 显示当前登录用户的：
    - 头像
    - 昵称 / 名字
    - 邮箱
  - 前端会把 Supabase 的 `access_token` 传给后端，后端使用 Supabase SDK 验证并落库。

### 用户管理

后端提供了一组 REST 接口（Python + Supabase）：

- `POST /auth/callback`  
  使用 `access_token` 从 Supabase 获取用户信息，写入/更新 `users` 表，并记录一条登录历史到 `login_events` 表。

- `GET /users`  
  返回所有用户列表。

- `GET /users/{id}`  
  获取单个用户详情。

- `PUT /users/{id}`  
  更新用户信息（目前主要是 `name` 字段）。

- `DELETE /users/{id}`  
  删除用户。

前端页面对应：

- “User Management” 区域：
  - `Load All Users`：查看所有用户
  - `Edit name`：修改指定用户的名称
  - `Delete`：删除用户

### 登录历史

- `GET /login-events`  
  返回最近若干条登录记录（email / provider / 登录时间）。

前端页面有 “Login History” 区域，可以表格方式查看历史登录记录。

### 登出

- 在 “Current User” 区域有 `Sign out` 按钮
- 点击后：
  - 调用 `supabase.auth.signOut()` 清理 Supabase session
  - 清空页面上的用户信息、用户列表和登录历史

---

## 3. 技术栈

**前端**

- 纯 HTML + CSS + 原生 JavaScript
- 使用 `@supabase/supabase-js@2` 进行 OAuth 登录和获取 session
- 部署在 GitHub Pages（`docs/` 目录为静态根目录）

**后端**

- Python 3
- Flask（提供 REST 接口）
- `supabase` Python SDK（访问 Supabase Auth 和数据库）
- `python-dotenv`（读取 `.env` 配置）
- `flask-cors`（简单的 CORS 配置）
- 部署在 PythonAnywhere（免费套餐）

**数据库 & 授权**

- Supabase Postgres 数据库
- Supabase Auth（GitHub / Google Provider）

---

## 4. 数据库设计（Supabase）

项目使用两张主要表：

### 4.1 `users`

存放“当前系统用户”的资料（和 Supabase Auth 的 user 对应）。

字段示例（简化）：

- `id`：与 Supabase Auth 的 `user.id` 一致（主键）
- `email`
- `name`
- `avatar_url`
- `provider`：github / google
- `created_at`
- `updated_at`

### 4.2 `login_events`

记录每一次登录，用于简单审计 / 历史查看。

字段示例：

- `id`：自增主键
- `auth_user_id`：对应 `users.id`
- `email`
- `provider`
- `logged_in_at`：登录时间（默认 `now()`）

后端在 `/auth/callback` 中，会：

1. Upsert 用户到 `users`
2. 同时插入一条记录到 `login_events`

---

## 5. 代码结构

大致目录（略）：

```text
.
├─ backend/           # Python 后端（Flask + Supabase）
│  ├─ app_flask.py    # Flask 入口
│  ├─ services.py     # 封装 Supabase 相关操作
│  ├─ requirements.txt
│  └─ .env            # 本地环境变量（不会提交到 GitHub）
└─ docs/              # 前端（GitHub Pages 静态资源）
   └─ index.html      # 登录页 + 用户管理 UI + 前端逻辑
