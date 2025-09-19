# HOI4 Mod 终极汉化工具



[![GitHub release](https://img.shields.io/github/v/release/your_username/HOI4-Ultimate-Translator)](https://github.com/your_username/HOI4-Ultimate-Translator/releases)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

终极解决方案，完美解决钢铁雄心4 Mod汉化中的格式问题、变量引用和专有名词保护！

##  ✨ 特色功能

- ✅ **智能格式修复**：自动处理缺失的`:0`标识符
-  🔗 **变量引用解析**：完美处理`$dam$`等引用格式
-  🛡️ **专有名词保护**：保护"Kiel"、"Panama"等专有名词
-  📊 **优先级处理系统**：确保基础术语先翻译
-  📝 **术语表学习**：自动记录并复用翻译结果
- 📋 **专业报告**：生成汉化质量评估报告

##  🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置设置
1. 编辑 `config/protected_terms.json` 添加专有名词
2. 获取 [DeepL API 密钥](https://www.deepl.com/pro-api)

### 运行工具
```python
python src/hoi4_translator.py
```

### 配置示例
```python
# === 用户配置区 ===
DEEPL_API_KEY = "YOUR_API_KEY_HERE"  # 替换为你的DeepL API密钥
MOD_DIRECTORY = r"FULL_PATH_TO_MOD_LOCALIZATION"  # 替换为mod本地化文件夹路径
MAX_WORKERS = 6  # 并发线程数(4-8)
# =================
```

## 📚 完整文档

[详细使用指南](docs/USER_GUIDE.md) | [故障排除](docs/TROUBLESHOOTING.md)

##  🧩 兼容性

| HOI4 版本 | 支持状态 |
|-----------|----------|
| 1.14.*    | ✅ 完全支持 |
| 1.13.*    | ✅ 支持 |
| 1.12.*    | ️ 基本支持 |

##  🤝 参与贡献

欢迎提交 Issue 和 Pull Request！请阅读我们的[贡献指南](CONTRIBUTING.md)。

## 📜 许可证

本项目采用 [MIT License](LICENSE)
