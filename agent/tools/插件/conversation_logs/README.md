# 对话记录器插件 v2.6 (conversation_logger)

全量捕获 AstrBot 对话日志，按 `unified_msg_origin` 分类存储。附带 **日记生成** 和 **文件管理** 两个 WebUI 页面。

## 存储结构

```
<data>/skills/diary/          ← 技能目录（首次启动自动创建）
├── SKILL.md
├── logs/                     ← 对话日志
│   └── <platform>/<origin>/<timestamp>.txt
│      例: webchat/webchat-FriendMessage-xxx/2026-06-20_1430.txt
├── prompts/                  ← 日记提示词模板
│   └── default.md            ← 自动创建
├── RAG/                      ← 生成的日记
│   └── 2026.06.20.txt
└── api/                      ← AI 提供商配置
    └── _模板.json            ← 复制编辑后生效
```

## WebUI 页面

| 页面 | 入口 | 功能 |
|------|------|------|
| **📝 日记生成** | 插件列表中「对话记录器」→「日记生成」 | 选日志→选模板→选AI→一键生成日记 |
| **📁 文件管理** | 插件列表中「对话记录器」→「文件管理」 | 浏览/编辑/删除 skill 下所有文件 |

## 指令

| 指令 | 说明 |
|------|------|
| `/logpath` | 显示插件目录路径和日志统计 |
| `/end` | 结束当前日志会话，下次对话自动新建文件 |

## 兼容性

- **AstrBot**: >= 4.0.0
- **依赖**: 仅 Python 标准库 + AstrBot 内置 API / aiohttp

## 安装

1. 将 `conversation_logs/` 放入 `data/plugins/`
2. WebUI 重载插件
3. 首次启动自动创建 skill 目录结构
4. 在插件列表中找到「对话记录器」使用

> 打包前清理 `__pycache__/`
