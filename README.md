# HOI4 Mod 终极汉化工具 - 超详细使用教程

## 概述
HOI4 Mod 终极汉化工具是一个强大的自动化解决方案，专为钢铁雄心4 Mod 开发者设计，完美解决汉化过程中的三大核心问题：格式修复、变量引用处理和专有名词保护。本工具基于 Python 开发，支持批量处理所有本地化文件。



## 功能特性
- ✅ **自动格式修复**：智能添加缺失的 `:0` 标识符
- 🔗 **变量引用解析**：完美处理 `$variable$` 格式引用
- 🛡️ **专有名词保护**：保护地名、组织名等不被翻译
- 📊 **优先级排序**：先处理基础词汇再处理复杂引用
- 📝 **术语表学习**：自动记录并复用翻译结果
- 📋 **质量报告**：生成汉化质量评估报告
- ⚡ **批量处理**：一键处理整个 Mod 的所有本地化文件

## 系统要求
- Python 3.8+
- DeepL API 密钥（免费版每月50万字符）
- 网络连接（用于调用 DeepL 翻译服务）

## 安装指南

### 1. 克隆仓库
```bash
git clone https://github.com/mcjsw-ALT/HOI4-Ultimate-Translator.git
cd HOI4-Ultimate-Translator
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 获取 DeepL API 密钥
1. 访问 [DeepL Pro](https://www.deepl.com/pro-api)
2. 注册/登录账号
3. 在账户设置中创建 API 密钥
4. 复制生成的密钥

## 配置说明

打开 `src/hoi4_translator.py` 文件，修改以下配置区域：

```python
# ===================== 用户配置区 =====================
DEEPL_API_KEY = "YOUR_API_KEY_HERE"# 替换为你的DeepL API密钥
MOD_DIRECTORY = r"C:\Steam\steamapps\workshop\content\394360\1234567890\localisation"# 替换为实际路径
MAX_WORKERS = 6# 并发线程数(4-8)
PROTECTED_TERMS_FILE = "config/protected_terms.json"# 专有名词保护列表
GLOSSARY_FILE = "config/translation_glossary.json"# 术语表文件
# ===================== 配置结束 =====================
```

### 路径说明
- **Steam 工坊 Mod**：
`C:\Steam\steamapps\workshop\content\394360\<Mod ID>\localisation`
- **本地 Mod**：
`C:\Users\<用户名>\Documents\Paradox Interactive\Hearts of Iron IV\mod\<Mod 名称>\localisation`

## 使用教程

### 1. 准备专有名词保护列表（可选）
编辑 `config/protected_terms.json`：
```json
[
"Kiel",
"Panama",
"NATO",
"Warsaw",
"Roosevelt",
"Churchill"
]
```

### 2. 准备术语表（可选）
编辑 `config/translation_glossary.json`：
```json
{
"dockyard": "dockyard:0 \"海军船坞\"",
"industrial_complex": "industrial_complex:0 \"民用工厂\"",
"arms_factory": "arms_factory:0 \"军工工厂\""
}
```

### 3. 运行汉化工具
```bash
python src/hoi4_translator.py
```

### 4. 查看处理过程
工具运行时将显示实时进度：
```
[INFO] 开始处理: common\buildings.txt
[DEBUG] 检测到未翻译条目: dam -> "水坝"
[DEBUG] 更新术语表: dam -> "水坝"
[DEBUG] 处理引用: $dam$ -> "水坝"
[SUCCESS] 完成 common\buildings.txt (32条目)
```

### 5. 处理完成后
1. 所有汉化文件将保存在原目录
2. 查看生成的报告：`translation_report.txt`
3. 检查更新的术语表：`config/translation_glossary.json`

## 输出文件说明

### 1. 汉化文件
- 与原始文件同名
- 保存在原始目录
- 格式为 UTF-8 with BOM

### 2. 汉化报告 (translation_report.txt)
```
===== 汉化质量报告 =====
处理时间: 2023-08-15 14:30:25
处理文件: 18个
总条目: 1,542
成功翻译: 1,510 (98.0%)
保护条目: 32 (2.0%)
术语表新增: 42条

===== 问题统计 =====
格式修复: 128处
变量引用处理: 76处
专有名词保护: 32处

===== 建议 =====
1. 检查保护列表是否需要更新
2. 验证军事术语翻译一致性
```

### 3. 更新后的术语表
自动添加新翻译的术语：
```json
{
"dockyard": "dockyard:0 \"海军船坞\"",
"industrial_complex": "industrial_complex:0 \"民用工厂\"",
"dam": "dam:0 \"水坝\"",
"nuclear_reactor": "nuclear_reactor:0 \"核反应堆\""
}
```

## 后期处理

### 1. 修改 .mod 文件
在 Mod 的 `.mod` 文件中添加：
```plaintext
supported_version = "1.14.*"
language = "l_simp_chinese"
```

### 2. 游戏内启用
1. 启动 HOI4
2. 进入 Mod 管理器
3. 启用您的汉化 Mod
4. 启动游戏验证汉化效果

## 高级功能

### 1. 自定义处理规则
在代码中找到 `process_line()` 函数，可添加自定义规则：
```python
def process_line(line):
# 示例：特殊处理军事术语
if "battalion" in line:
return line.replace("battalion", "营")

# 原始处理逻辑...
```

### 2. 多语言支持
修改配置支持其他语言：
```python
TARGET_LANG = "ZH"# 简体中文
# 可选值: EN(英语), DE(德语), FR(法语), ES(西班牙语), JA(日语)
```

### 3. 增量汉化
工具会自动跳过已翻译条目，只处理新增或修改内容

## 常见问题解决

### 问题1：API 密钥无效
**现象**：
```
[ERROR] DeepL 认证失败: 请检查API密钥
```
**解决**：
1. 确认密钥正确复制
2. 访问 [DeepL 账户](https://www.deepl.com/pro-account) 检查密钥状态
3. 确保账户有足够配额

### 问题2：文件编码错误
**现象**：
```
[ERROR] 文件编码错误: buildings.yml
```
**解决**：
1. 用 VS Code 打开文件
2. 右下角点击编码 → 保存为 UTF-8 with BOM
3. 重新运行工具

### 问题3：变量引用未解析
**现象**：
```
$dam$ 未被替换
```
**解决**：
1. 检查术语表中是否有对应条目
2. 确保原始文件中有定义 `dam: "Dam"`
3. 手动添加到术语表

### 问题4：专有名词被翻译
**解决**：
1. 编辑 `protected_terms.json`
2. 添加需要保护的术语
3. 重新运行工具

## 最佳实践建议

1. **版本控制**：
- 使用 Git 管理汉化过程
- 每次更新前提交原始文件

2. **分批处理**：
```bash
# 先处理核心文件
python src/hoi4_translator.py --files common/technology.txt

# 再处理其他文件
python src/hoi4_translator.py --exclude common/technology.txt
```

3. **术语表维护**：
- 定期审查术语表
- 分享术语表给团队其他成员
- 为大型项目建立统一术语库

## 贡献指南
欢迎提交改进方案：
1. Fork 本项目仓库
2. 创建特性分支 (`git checkout -b feature/improvement`)
3. 提交更改 (`git commit -am 'Add some feature'`)
4. 推送分支 (`git push origin feature/improvement`)
5. 创建 Pull Request

## 技术支持
遇到问题？请提交 Issue：
https://github.com/mcjsw-ALT/HOI4-Ultimate-Translator/issues

---
**立即开始您的汉化之旅！**
让全球中文玩家享受您精心制作的 Mod！
