import os
import re
import requests
import shutil
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class HOI4AdvancedTranslator:
    def __init__(self, api_key, source_lang="EN", target_lang="ZH", max_workers=4):
        """
        HOI4 Mod高级汉化工具
        解决格式问题、变量引用和专有名词保护
        """
        self.api_key = api_key
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_workers = max_workers
        self.endpoint = "https://api-free.deepl.com/v2/translate"
        # 增强的正则表达式，支持缺失:0的情况
        self.text_regex = re.compile(r'^(\s*[^\s:]+(?::\d+)?\s+)(".*?")$', re.MULTILINE)
        self.var_regex = re.compile(r'(\$[^\s]+\$|§.)')
        self.processed_count = 0
        self.error_count = 0
        self.translation_map = {}  # 存储翻译结果用于引用替换
        self.protected_terms = ["Kiel", "Panama", "Dam"]  # 专有名词保护列表
        self.format_fixes = 0  # 格式修复计数器

    def _replace_vars_with_placeholders(self, text):
        """保护游戏变量和专有名词"""
        replacements = {}
        placeholder_template = "__HOI4_VAR_{}__"
        
        def replace_match(match):
            var = match.group(0)
            placeholder = placeholder_template.format(len(replacements))
            replacements[placeholder] = var
            return placeholder
        
        # 第一步：保护专有名词
        for term in self.protected_terms:
            text = text.replace(term, f"__PROTECTED_{term}__")
        
        # 第二步：保护游戏变量
        processed_text = self.var_regex.sub(replace_match, text)
        return processed_text, replacements

    def _restore_vars_from_placeholders(self, text, replacements):
        """恢复原始变量和专有名词"""
        # 先恢复游戏变量
        for placeholder, var in replacements.items():
            text = text.replace(placeholder, var)
        
        # 再恢复专有名词
        for term in self.protected_terms:
            text = text.replace(f"__PROTECTED_{term}__", term)
        
        return text

    def _fix_missing_colon_zero(self, line):
        """自动修复缺失的:0格式问题"""
        if re.match(r'^\s*[a-zA-Z0-9_]+:?\s+"', line) and ':0' not in line:
            self.format_fixes += 1
            return line.replace('"', ':0 "', 1)
        return line

    def _translate_text(self, text):
        """增强翻译功能"""
        if not text.strip() or text.strip().startswith("#"):
            return text
        
        # 修复缺失:0格式
        fixed_line = self._fix_missing_colon_zero(text)
        if fixed_line != text:
            text = fixed_line
        
        # 提取键名
        key_match = re.match(r'^\s*([^\s:]+):', text)
        key = key_match.group(1) if key_match else None
        
        # 保护变量和专有名词
        processed_text, replacements = self._replace_vars_with_placeholders(text)
        
        headers = {"Authorization": f"DeepL-Auth-Key {self.api_key}"}
        data = {
            "text": processed_text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "preserve_formatting": "1"
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            translated_text = result['translations'][0]['text']
            restored_text = self._restore_vars_from_placeholders(translated_text, replacements)
            
            # 记录翻译结果用于引用处理
            if key:
                self.translation_map[key] = restored_text
            
            return restored_text
        
        except Exception as e:
            print(f"\n翻译出错: {str(e)}")
            self.error_count += 1
            return text

    def _process_references(self, content):
        """处理变量引用（如$dam$）"""
        # 查找所有引用模式
        ref_matches = re.finditer(r'(\$[^\s]+\$)', content)
        
        for match in ref_matches:
            ref_key = match.group(0).strip('$')
            # 查找被引用的翻译
            if ref_key in self.translation_map:
                # 提取翻译文本（去掉键和引号）
                ref_translation = self.translation_map[ref_key]
                value_match = re.search(r':\d+\s+"(.*?)"$', ref_translation)
                if value_match:
                    translated_value = value_match.group(1)
                    content = content.replace(match.group(0), translated_value)
        
        return content

    def _process_yaml_file(self, file_path):
        """处理单个本地化文件"""
        try:
            # 重置翻译映射
            self.translation_map = {}
            self.format_fixes = 0
            
            # 创建备份
            backup_path = f"{file_path}.backup"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 预处理：识别并标记需要翻译的行
            lines = content.split('\n')
            translated_lines = []
            
            # 处理每一行
            for line in lines:
                if self.text_regex.match(line) or re.match(r'^\s*[^\s:]+:?\s+"', line):
                    translated_line = self._translate_text(line)
                    translated_lines.append(translated_line)
                else:
                    translated_lines.append(line)
            
            # 合并处理后的内容
            translated_content = '\n'.join(translated_lines)
            
            # 处理引用（如$dam$）
            translated_content = self._process_references(translated_content)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            self.processed_count += 1
            return self.format_fixes
        
        except Exception as e:
            print(f"\n处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
            self.error_count += 1
            return 0

    def process_directory(self, directory_path):
        """处理目录中的所有yml文件"""
        yaml_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.yml'):
                    yaml_files.append(os.path.join(root, file))
        
        total_files = len(yaml_files)
        print(f"找到 {total_files} 个本地化文件")
        
        if not yaml_files:
            print("未找到YML文件! 请检查路径是否正确")
            return
        
        print("开始翻译(包含格式修复和引用处理)...")
        total_fixes = 0
        with tqdm(total=total_files, desc="汉化进度", unit="file") as pbar:
            for file_path in yaml_files:
                fixes = self._process_yaml_file(file_path)
                total_fixes += fixes
                pbar.set_postfix({"修复": fixes})
                pbar.update(1)
        
        # 生成报告
        print("\n" + "="*50)
        print(f"汉化完成! 成功处理: {self.processed_count}/{total_files} 个文件")
        print(f"格式修复: {total_fixes} 处")
        print(f"错误文件: {self.error_count} 个")
        print(f"原始文件已备份为 .backup 扩展名")
        print("="*50)
        print("翻译质量提示:")
        print("1. 变量引用(如$dam$)已自动替换为翻译文本")
        print("2. 专有名词(Kiel, Panama等)已受到保护")
        print("3. 缺失的:0标识符已自动修复")
        print("="*50)
        print("下一步:")
        print("1. 在.mod文件中添加: language = \"l_simp_chinese\"")
        print("2. 在游戏中测试翻译效果")
        print("3. 如有需要，手动调整专有名词翻译")
        print("="*50)

# ===== 用户配置区 =====
DEEPL_API_KEY = "YOUR_API_KEY_HERE"  # 替换为你的DeepL API密钥
MOD_DIRECTORY = r"FULL_PATH_TO_YOUR_MOD_LOCALIZATION"  # 替换为mod本地化文件夹路径
# ======================

if __name__ == "__main__":
    print("="*50)
    print("HOI4 Mod高级汉化工具 v2.0")
    print("="*50)
    
    # 配置检查
    if DEEPL_API_KEY == "YOUR_API_KEY_HERE" or MOD_DIRECTORY == "FULL_PATH_TO_YOUR_MOD_LOCALIZATION":
        print("错误: 请先修改脚本中的配置信息!")
        print("1. 打开本脚本文件")
        print("2. 修改顶部的DEEPL_API_KEY和MOD_DIRECTORY")
        print("3. 保存后重新运行")
        input("\n按Enter键退出...")
        sys.exit()
    
    # 路径验证
    if not os.path.exists(MOD_DIRECTORY):
        print(f"错误: 路径不存在 - {MOD_DIRECTORY}")
        print("请检查路径是否正确")
        input("\n按Enter键退出...")
        sys.exit()
    
    # 实例化并运行
    try:
        translator = HOI4AdvancedTranslator(api_key=DEEPL_API_KEY)
        translator.process_directory(MOD_DIRECTORY)
    except Exception as e:
        print(f"\n程序运行错误: {str(e)}")
    
    input("\n按Enter键退出程序...")