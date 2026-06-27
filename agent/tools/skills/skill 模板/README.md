# 🧩 Hermes Agent Skill 模板

本目录是创建 **Hermes Agent 技能（Skill）** 的起点模板。复制 `SKILL（模板）.md` 后按需修改即可。

## 用法

1. 将 `SKILL（模板）.md` 复制到目标位置：
   ```bash
   cp "SKILL（模板）.md" /opt/data/skills/<分类>/<你的技能名>/SKILL.md
   ```
2. 替换占位内容：`name`、`description`、各章节内容
3. 按需使用下面的子文件夹存放辅助文件

## 子文件夹说明

| 文件夹 | 用途 | 存放什么 |
|--------|------|---------|
| **`references/`** | 参考文档 | 技术笔记、API 文档、配置说明、FAQ 等 `.md` 文档 |
| **`templates/`** | 模板文件 | 配置文件模板、YAML/JSON 示例、代码片段等 |
| **`scripts/`** | 可执行脚本 | 安装脚本、验证脚本、自动化工具（`.sh` / `.py`） |
| **`assets/`** | 资源文件 | 图片、图标、字体、音频等静态资源 |

### 在 SKILL.md 中引用

```markdown
<!-- 引用参考文档 -->
详见 `references/deployment-guide.md`。

<!-- 引用配置模板 -->
将 `templates/config.example.yaml` 复制为 `config.yaml` 并修改。

<!-- 引用脚本 -->
运行 `scripts/setup.sh` 初始化环境。
```

通过 `skill_view(name, file_path)` 可随时读取这些文件：

```
skill_view(name='your-skill', file_path='references/api-docs.md')
skill_view(name='your-skill', file_path='scripts/validate.py')
```

## 完整技能目录示例

```
skills/<分类>/<技能名>/
├── SKILL.md              # 主技能文件（必需）
├── references/           # 参考文档
│   ├── api-docs.md
│   └── troubleshooting.md
├── templates/            # 模板文件
│   └── config.example.yaml
├── scripts/              # 可执行脚本
│   ├── setup.sh
│   └── validate.py
└── assets/               # 资源文件
    └── logo.png
```

## 小提示

- SKILL.md 超过 **20,000 字符** 时建议拆分内容到 `references/`
- `scripts/` 中的脚本可通过 `terminal()` 直接运行
- `assets/` 中的图片可通过 `vision_analyze()` 加载分析
- 如果某个文件夹暂时没用上，可以留着空的，以后扩展
