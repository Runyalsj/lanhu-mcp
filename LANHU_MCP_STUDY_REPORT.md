# Lanhu MCP 项目学习报告

更新日期：2026-05-29  
工作区：`/Users/potato/Rylsj/mcps/lanhu-mcp`

## 1. 我确认到的仓库地址

### 上游项目地址

- 官方/文档指向仓库：`https://github.com/dsphper/lanhu-mcp`
- `pyproject.toml` 中的 `Homepage`、`Repository`、`Documentation` 也都指向 `dsphper/lanhu-mcp`

### 当前本地仓库地址

- 当前工作区 `git remote origin`：
  - `git@github.com:Runyalsj/lanhu-mcp.git`

### 结论

你现在本地打开的是一个 **fork 仓库工作区**，但项目文档、包元数据和对外介绍仍然以上游仓库 `dsphper/lanhu-mcp` 为准。

## 2. 这个项目到底是干什么的

这是一个基于 **FastMCP + Python + Playwright** 的蓝湖 MCP 服务，主要解决三类问题：

1. 让 AI 直接读取蓝湖中的 **需求文档 / Axure 原型**
2. 让 AI 直接读取蓝湖中的 **UI 设计稿 / 切图资源**
3. 提供一个 **团队留言板 / 知识库**，让不同 IDE 里的 AI 共享上下文

它本质上不是一个普通网页爬虫，而是一个面向 AI 助手的 MCP Server。  
AI 客户端通过 HTTP 或 stdio 连接它，然后调用它暴露的工具。

## 3. 核心能力总览

### A. 需求文档分析

- 读取蓝湖产品文档、Axure 原型页面
- 先列页面，再分析页面
- 支持三种分析视角：
  - `developer`：开发视角
  - `tester`：测试视角
  - `explorer`：快速探索/评审视角
- 内置“四阶段工作流”：
  - Stage 1：全局文本扫描
  - Stage 2：按模块分组深度分析
  - Stage 3：反向校验
  - Stage 4：生成交付文档

### B. UI 设计稿分析

- 拉取设计图列表
- 分析具体设计图
- 返回：
  - 设计图预览
  - 文本信息
  - 设计样式参考
  - 由设计 schema 转出的 HTML + CSS

这意味着它不只是“看图说话”，而是能把蓝湖设计结构化成更适合 AI 生成代码的输入。

### C. 切图与素材提取

- 从单个设计图中提取切图信息
- 返回多倍率下载地址：
  - Web `1x/2x/3x`
  - iOS `@1x/@2x/@3x`
  - Android `mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi`
- 内置一套给 AI 的工作流提示，要求 AI 先问用户平台/倍率，再决定下载策略

### D. 团队留言板

- 留言、编辑、删除、查询
- 支持消息类型：
  - `normal`
  - `task`
  - `question`
  - `urgent`
  - `knowledge`
- 支持跨项目全局搜索
- 支持 `@人名` 和飞书 webhook 通知
- 自动记录哪些协作者的 AI 访问过某个项目

## 4. 服务运行方式

项目支持两种 MCP 运行模式。

### HTTP 模式

默认模式。启动方式：

```bash
python lanhu_mcp_server.py
```

默认会启动在：

```text
http://localhost:8000/mcp
```

### stdio 模式

适合 Cursor、Claude Code 这类本地按需拉起 MCP 的客户端。  
启动方式依赖：

```bash
./run-stdio.sh
```

实际逻辑是：

- 进入项目目录
- 设置 `MCP_TRANSPORT=stdio`
- 执行 `./venv/bin/python lanhu_mcp_server.py`

这说明该脚本默认假设你已经在项目根目录创建了 `venv`。

## 5. 配置项梳理

我结合 `config.example.env` 和服务端代码，把有效配置项整理如下。

### 必需配置

```env
LANHU_COOKIE="your_lanhu_cookie_here"
```

用途：

- 访问蓝湖 API
- 打开邀请链接并完成重定向
- 拉取 PRD、设计图、切图等内容

没有它，这个服务基本不可用。

### 可选配置

```env
SERVER_HOST="0.0.0.0"
SERVER_PORT=8000
FEISHU_WEBHOOK_URL=""
DATA_DIR="./data"
HTTP_TIMEOUT=30
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
DEBUG="false"
```

### 代码中还能看到的相关配置

- `MCP_TRANSPORT`
  - `http`：默认
  - `stdio`：给本地 MCP 客户端按需拉起
- `DDS_COOKIE`
  - 默认回退到 `LANHU_COOKIE`
- 用户身份来源
  - HTTP 模式：从 MCP URL query 中取 `role` / `name`
  - stdio 模式：从环境变量取 `LANHU_USER_ROLE` / `LANHU_USER_NAME`

## 6. 目录和数据落点

运行后主要数据会落在：

- `data/`
  - 页面资源缓存
  - 截图缓存
  - 留言 JSON 数据
  - 设计稿缓存
- `logs/`
  - 运行日志

README 中的架构和代码实现都说明了一个关键点：  
这个项目很依赖本地缓存，尤其是：

- 文档版本号缓存
- 页面截图缓存
- 资源增量更新

这也是它性能优化的核心。

## 7. MCP 工具清单与正确调用顺序

## 7.1 需求文档类

### `lanhu_resolve_invite_link`

用途：

- 把分享/邀请链接解析成真正可用的蓝湖项目地址

适用场景：

- 用户给的是 `invite?sid=xxx` 这种分享链接

### `lanhu_list_product_documents`

用途：

- 列出某个项目下的所有产品文档 / PRD / 原型文档

适用场景：

- 只知道项目，不知道具体 `docId`

### `lanhu_get_pages`

用途：

- 获取某个 PRD / Axure 文档的页面列表

这是需求分析前的第一步工具。

### `lanhu_get_ai_analyze_page_result`

用途：

- 获取页面分析结果

关键参数：

- `page_names`
  - 可传单页名
  - 可传数组
  - 可传 `all`
- `mode`
  - `text_only`
  - `full`
- `analysis_mode`
  - `developer`
  - `tester`
  - `explorer`

推荐工作流：

1. `lanhu_get_pages`
2. `lanhu_get_ai_analyze_page_result(..., page_names="all", mode="text_only")`
3. 让用户选择 `analysis_mode`
4. 按模块分组调用 `mode="full"`
5. 汇总生成交付物

## 7.2 设计稿类

### `lanhu_get_designs`

用途：

- 获取 UI 设计图列表

这是设计分析前的第一步工具。

### `lanhu_get_ai_analyze_design_result`

用途：

- 分析具体设计图

关键点：

- `design_names` 可以传：
  - `all`
  - 列表
  - 精确设计图名称
  - 列表中的序号
- 返回的不只是图片，还包含 HTML + CSS 参考代码

代码里强调了一个重要原则：

- **HTML + CSS 是设计参数的最高优先级来源**
- 图片只用于视觉核对，不应该反向覆盖 CSS 数值

## 7.3 切图类

### `lanhu_get_design_slices`

用途：

- 从单个设计图中提取切图和下载地址

关键参数：

- `design_name`
  - 文档注释说要“精确匹配”
  - 但代码实际比文档更宽松，支持：
    - 序号
    - 精确名称
    - 引号归一化后匹配
    - 唯一子串匹配
    - URL 里的 `image_id` 回退匹配

这是一个典型“代码能力比 README 写得更强”的地方。

## 7.4 留言板类

### `lanhu_say`

- 发布留言
- 可带 `mentions`
- 可带 `message_type`

### `lanhu_say_list`

- 查询留言
- 支持：
  - 单项目查询
  - 全局查询 `url='all'`
  - 类型过滤 `filter_type`
  - 正则搜索 `search_regex`
  - 限量 `limit`

### `lanhu_say_detail`

- 按消息 ID 查询详情
- 支持单个 ID 或数组

### `lanhu_say_edit`

- 编辑留言标题/内容/@列表

### `lanhu_say_delete`

- 删除留言

### `lanhu_get_members`

- 查看某项目下被记录到的协作者

## 8. 使用技巧

下面这些不是 README 表面的“使用方法”，而是我从文档和代码里整理出的实战建议。

### 技巧 1：需求分析一定要先跑 Stage 1

不要一上来就对全部页面做 `full` 分析。  
正确姿势是先：

```text
page_names="all" + mode="text_only"
```

这样能先建立模块视图，再决定分组，否则：

- token 很容易炸
- 页面多时效果差
- 用户也没机会先选分析视角

### 技巧 2：让用户显式选择分析视角

这个项目在代码里非常强地约束了需求分析流程：  
Stage 1 后，应该让用户选：

- 开发视角
- 测试视角
- 快速探索

如果跳过这个动作，虽然工具仍可调用，但会偏离项目作者设计的理想工作流。

### 技巧 3：设计稿分析时，优先相信 HTML + CSS，不要只盯着图片

`lanhu_get_ai_analyze_design_result` 的设计意图非常明确：

- 样式数值以返回的 HTML/CSS 为准
- 图片只用来校验视觉结果

这对于让 AI 生成代码时避免“猜颜色、猜字号、猜间距”很重要。

### 技巧 4：切图下载前一定先确认倍率

代码内置的 AI workflow 明确要求：

- 先向用户确认平台和倍率
- 再执行下载

默认推荐值是：

- **Web 2x**

因为它通常最直接，且复用原图 URL。

### 技巧 5：留言查询必须主动加筛选

`lanhu_say_list` 已经在代码里处理“上下文爆炸”问题了。  
建议优先组合：

- `filter_type`
- `search_regex`
- `limit`

尤其全局查询时，最好不要无条件“查全部”。

### 技巧 6：URL 里的 `role` / `name` 最好用英文

README 已明确提醒：部分 MCP 客户端对 URL 中文参数兼容不好。  
因此 HTTP 连接建议类似：

```text
http://localhost:8000/mcp?role=Developer&name=YourName
```

### 技巧 7：本地客户端优先考虑 stdio，而不是常驻 HTTP

如果你是在 Cursor / Claude Code / Windsurf 本机里用它，stdio 模式更贴近 MCP 的典型接入方式：

- 不必额外常驻服务
- 客户端按需拉起
- 环境变量可直接注入身份信息

前提是你要保证：

- 已创建 `venv`
- `venv` 内依赖已安装

### 技巧 8：角色映射是模糊归一化的

代码里对角色做了 `ROLE_MAPPING_RULES` 归一化，例如：

- `java/python/go/backend` 会归到“后端”
- `react/vue/js/css` 会归到“前端”
- `ios/android/flutter` 会归到“客户端”

这意味着用户传的角色文本不必完全标准，但最好仍尽量稳定。

## 9. 当前实现中的注意点和坑

这是这次阅读里最值得你后续关注的部分。

### 9.1 `run-stdio.sh` 强依赖 `./venv/bin/python`

这意味着如果你不是按项目预期方式建虚拟环境，而是：

- 全局 Python
- `uv`
- 其他解释器路径

那这个脚本会直接失效。

### 9.2 `easy-install.sh` 里引用的是 `.env.example`

但当前仓库实际存在的是：

```text
config.example.env
```

也就是说，`easy-install.sh` 里这一段存在明显不一致：

- 脚本想复制 `.env.example`
- 仓库里没有这个文件

这会影响“一键安装”的可靠性。

### 9.3 依赖声明有版本不一致

我看到两个地方对 `fastmcp` 的要求不同：

- `pyproject.toml`：`fastmcp>=0.2.0`
- `requirements.txt`：`fastmcp>=2.0.0`

这说明包元数据和实际安装依赖没有完全同步，后续如果要发布或打包，最好统一。

### 9.4 飞书提醒名单是示例数据，不是开箱即用

代码里的：

- `MENTION_ROLES`
- `FEISHU_USER_ID_MAP`

都是示例值。  
如果不替换成你们团队真实成员：

- `@提醒` 校验会受限
- 飞书通知也不具备真正可用性

### 9.5 Docker Compose 端口写死为 `8000:8000`

虽然 `.env` 有 `SERVER_PORT`，但 `docker-compose.yml` 的宿主机映射仍固定写了 `8000:8000`。  
如果本机 8000 被占用，你需要手工改 compose 文件，而不只是改 `.env`。

### 9.6 这是一个“视觉能力优先”的 MCP

README 和代码都强调：

- 必须使用支持视觉的模型
- 文本模型不适合这个项目

所以如果后续你把它接到纯文本能力弱的模型上，结果质量会明显下降。

## 10. 我对这个项目的整体判断

这个项目的定位很清晰，不是通用型 MCP，而是一个很强的 **蓝湖专用 AI 协作中间层**。  
它最有价值的不是“抓取蓝湖数据”本身，而是把蓝湖内容重新组织成 AI 更容易消费的工作流：

1. 需求分析工作流
2. 设计还原工作流
3. 团队知识共享工作流

如果后续你要真正用起来，我建议你按下面优先级理解和接入：

1. 先打通 `LANHU_COOKIE` 和基础 HTTP/stdio 连接
2. 再跑通 PRD 分析链路
3. 再跑通设计稿与切图链路
4. 最后才启用留言板和飞书通知

因为前三步解决的是“AI 看得懂蓝湖”，最后一步解决的是“多个 AI 共享上下文”。

## 11. 建议你下一步关注的文件

- `README.md`
  - 总体说明最全
- `lanhu_mcp_server.py`
  - 所有核心逻辑都在这里
- `config.example.env`
  - 环境变量基线
- `run-stdio.sh`
  - 本地 MCP 客户端接入关键
- `docker-compose.yml`
  - 服务部署关键
- `easy-install.sh`
  - 当前安装流程里最容易暴露脚本/文档不一致问题的地方

## 12. 本报告依据

本报告基于以下信息整理：

- 本地代码仓库 `Runyalsj/lanhu-mcp`
- 上游项目 README：`https://github.com/dsphper/lanhu-mcp`
- 本地关键文件：
  - `README.md`
  - `pyproject.toml`
  - `requirements.txt`
  - `config.example.env`
  - `docker-compose.yml`
  - `run-stdio.sh`
  - `easy-install.sh`
  - `setup-env.sh`
  - `lanhu_mcp_server.py`

