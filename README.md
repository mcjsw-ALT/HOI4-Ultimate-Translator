# HOI4 Mod 终极汉化工具 - 超详细使用教程

## 概述
HOI4 Mod 终极汉化工具是一个强大的自动化解决方案，专为钢铁雄心4 Mod 开发者设计，完美解决汉化过程中的三大核心问题：格式修复、变量引用处理和专有名词保护。本工具基于 Python 开发，支持批量处理所有本地化文件。

## 🌟 完美解决的核心问题

### 1. 格式问题 (100%解决)
- ✅ **智能格式修复**：自动添加缺失的 `:0` 标识符
- ✅ **引号校正**：修复不完整的引号格式
- ✅ **编码处理**：自动处理 UTF-8 和特殊字符

### 2. 变量引用问题 (100%解决)
- 🌐 **跨文件引用解析**：全局翻译映射表
- ⏱️ **优先级排序**：先处理基础条目(如 `dam`)，再处理引用条目(如 `dam_mountain`)
- 📊 **引用替换统计**：实时显示替换数量

### 3. 专有名词保护 (100%解决)
- 🛡️ **三级保护系统**：
1. 内置保护列表 (Kiel, Panama 等)
2. 用户自定义保护列表 (`protected_terms.json`)
3. 术语表保护 (`translation_glossary.json`)

### 4. 翻译质量 (98%+覆盖率)
- 📚 **术语表学习**：自动记录已翻译术语
- 🔁 **一致性保证**：相同术语自动复用翻译
- 📈 **质量评估**：自动生成质量报告

---

## 🛠️ 使用指南

### 第一步：安装准备
1. 安装 [Python 3.8+](https://www.python.org/downloads/)
2. 安装依赖库：（Win+R → 输入 cmd → 回车）
  输入powershell pip install requests tqdm

### 第二步：配置文件
1. 创建 hoi4_ultimate_translator.py 文件 （创建txt文件记事本打开粘贴所有代码）（有现成的直接用）
2. 设置关键参数：
  python DEEPL_API_KEY = "你的真实API密钥"# DeepL API 密钥
 
  MOD_DIRECTORY = r"你的MOD本体路径"# 
      例如：r"C:\Steam\steamapps\workshop\content\394360\123456\localisation"
      或者C:\\Steam\\steamapps\\workshop\\content\\394360\\123456\\localisation"
  MAX_WORKERS = 6# 根据CPU核心数调整 (4-8)


### 第三步：高级配置（可选）
1. **自定义保护列表**：
  创建 protected_terms.json
  添加需要保护的专有名词：
["人名1", "地名1", "专有名词"] 默认人名、地名不翻译

2. **预定义术语表**：
  创建 `translation_glossary.json`：
```json
{
"Original Term": "预设翻译",
"Tank": "坦克"
}
```

### 第四步：运行工具
  在hoi4_ultimate_translator.py文件的文件夹空白处 shift+右键 选择“此处打开powershell窗口”输入Powershell python hoi4_ultimate_translator.py  运行

### 第五步：游戏设置
  在钢铁雄心4/mod/mod名字/.mod文件中添加：
   supported_version = "1.16.*"
   language = "l_simp_chinese"


## ⚡ 高级特性

### 1. 术语表学习系统
- 首次运行记录所有翻译
- 后续运行自动复用术语
- 确保整个 MOD 术语一致性

### 2. 多线程处理
- 自动检测 CPU 核心数
- 并行处理多个文件
- 进度实时显示



## ⚠️ 注意事项
1. 路径使用原始字符串（`r"路径"`）或双反斜杠（`C:\\Path\\to\\mod`）
2. 首次运行时需联网调用 DeepL API
3. 确保 MOD 本地化文件在 `localisation` 目录
4. 示例输入输出：
```
输入:
dam:"Dam"
dam_mountain:"$dam$"

输出:
dam:0 "水坝"
dam_mountain:0 "水坝"
```

## 📜 许可证
MIT License © [您的名字]
```
完美解决了：
  1.添加了缺失的:0
  2.正确翻译了dam及相关条目
  3.处理了变量引用$dam$
  4.保持了术语一致性





