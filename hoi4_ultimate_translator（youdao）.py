import os
import re
import requests
import shutil
import sys
import json
import time
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class HOI4UltimateTranslator:
    def __init__(self, app_key, app_secret, source_lang="EN", target_lang="ZH", max_workers=4):
        """
        HOI4 Mod终极汉化工具 v3.1
        使用友道翻译API，添加速率限制功能
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_workers = max_workers
        self.endpoint = "https://openapi.youdao.com/api"
        
        # 速率限制设置（友道API免费版限制为1次/秒）
        self.rate_limit_delay = 1.2  # 每次请求之间的延迟（秒）
        self.last_request_time = 0
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 5  # 重试延迟（秒）
        
        # 智能正则表达式系统
        self.text_regex = re.compile(r'^(\s*[^\s:]+(?::\d+)?\s+)(".*?")$', re.MULTILINE)
        self.var_regex = re.compile(r'(\$[^\s]+\$|§.)')
        self.key_extract_regex = re.compile(r'^\s*([^\s:]+)')
        
        # 统计系统
        self.processed_count = 0
        self.error_count = 0
        self.format_fixes = 0
        self.reference_replacements = 0
        self.protected_count = 0
        self.api_errors = 0
        self.rate_limited = 0
        
        # 智能缓存系统
        self.translation_map = {}
        self.global_translation_map = {}
        self.protected_terms = self.load_protected_terms()
        self.glossary = self.load_glossary()
        
        # 智能排序系统
        self.file_priority = {
            "l_english.yml": 0,
            "l_simp_chinese.yml": 100
        }

    # ... (load_protected_terms, load_glossary, save_glossary等方法保持不变)
    
    def _call_youdao_api(self, text):
        """调用友道翻译API并处理速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # 确保符合速率限制
        if elapsed < self.rate_limit_delay:
            delay = self.rate_limit_delay - elapsed
            time.sleep(delay)
        
        # 生成API请求参数
        salt = str(uuid.uuid1())
        curtime = str(int(time.time()))
        sign_str = self.app_key + self._truncate_text(text) + salt + curtime + self.app_secret
        sign = hashlib.sha256(sign_str.encode()).hexdigest()
        
        params = {
            'q': text,
            'from': self.source_lang,
            'to': self.target_lang,
            'appKey': self.app_key,
            'salt': salt,
            'sign': sign,
            'signType': 'v3',
            'curtime': curtime
        }
        
        # 带重试机制的API请求
        for attempt in range(self.max_retries):
            try:
                self.last_request_time = time.time()
                response = requests.get(self.endpoint, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                # 错误处理
                error_code = result.get('errorCode', '0')
                if error_code != '0':
                    error_msg = self._decode_youdao_error(error_code)
                    print(f"\n友道API错误 ({error_code}): {error_msg}")
                    self.api_errors += 1
                    
                    # 如果是速率限制错误，等待更长时间
                    if error_code in ['103', '108', '110', '111']:
                        print(f"达到速率限制，等待 {self.retry_delay} 秒后重试...")
                        self.rate_limited += 1
                        time.sleep(self.retry_delay)
                        continue
                    
                    # 如果重试次数用完，返回原文
                    if attempt == self.max_retries - 1:
                        return text
                else:
                    # 返回翻译结果
                    return result['translation'][0]
            
            except requests.exceptions.RequestException as e:
                print(f"\nAPI请求失败: {str(e)}")
                self.api_errors += 1
                # 最后一次尝试后返回原文
                if attempt == self.max_retries - 1:
                    return text
                # 等待后重试
                time.sleep(self.retry_delay)
        
        return text
    
    def _truncate_text(self, text, max_len=20):
        """截断长文本以满足友道API签名要求"""
        if not text:
            return ""
        size = len(text)
        if size <= max_len:
            return text
        return text[:10] + str(size) + text[-10:]
    
    def _decode_youdao_error(self, error_code):
        """友道API错误代码解码"""
        errors = {
            '101': '缺少必填参数',
            '102': '不支持的语言类型',
            '103': '翻译文本过长',
            '104': '不支持的API类型',
            '105': '不支持的签名类型',
            '106': '不支持的响应类型',
            '107': '不支持的传输加密类型',
            '108': '应用ID无效',
            '109': 'batchLog格式不正确',
            '110': '无相关服务有效实例',
            '111': '开发者账号无效',
            '201': '解密失败',
            '202': '签名检验失败',
            '203': '访问IP地址不在可访问IP列表',
            '301': '辞典查询失败',
            '302': '翻译查询失败',
            '303': '服务端异常',
            '401': '账户已经欠费',
            '411': '访问频率受限'
        }
        return errors.get(error_code, f"未知错误 ({error_code})")
    
    # ... (_replace_special_content, _restore_special_content, _fix_format_issues等方法保持不变)
    
    def _translate_text(self, text):
        """智能翻译引擎（使用友道API）"""
        if not text.strip() or text.strip().startswith("#"):
            return text
        
        # 修复格式问题
        original_text = text
        text = self._fix_format_issues(text)
        
        # 提取键名
        key_match = self.key_extract_regex.match(text)
        key = key_match.group(1).strip() if key_match else None
        
        # 保护特殊内容
        protected_text, replacements = self._replace_special_content(text)
        
        # 检查是否在术语表中
        if key and key in self.glossary:
            return self.glossary[key]
        
        # 使用友道API翻译
        try:
            translated_text = self._call_youdao_api(protected_text)
            
            # 恢复特殊内容
            final_text = self._restore_special_content(translated_text, replacements)
            
            # 添加到术语表
            if key and key not in self.glossary:
                self.glossary[key] = final_text
            
            return final_text
        
        except Exception as e:
            print(f"\n翻译出错: {str(e)}")
            self.error_count += 1
            return original_text
    
    # ... (_process_references, _process_yaml_file, process_directory等方法保持不变)
    
    def generate_report(self, total_files, total_fixes):
        """生成终极质量报告（添加API错误统计）"""
        report = [
            "=" * 70,
            "HOI4 MOD 汉化终极报告 (友道API版)",
            "=" * 70,
            f"处理文件总数: {total_files}",
            f"成功处理文件: {self.processed_count}",
            f"错误文件数: {self.error_count}",
            "-" * 70,
            f"API请求错误: {self.api_errors} 次",
            f"速率限制触发: {self.rate_limited} 次",
            f"自动格式修复: {total_fixes} 处",
            f"变量引用替换: {self.reference_replacements} 处",
            f"专有名词保护: {self.protected_count} 处",
            f"术语表条目: {len(self.glossary)} 个",
            "=" * 70,
            "翻译质量评估:"
        ]
        
        # ... (质量评估部分保持不变)
        
        report.extend([
            "=" * 70,
            "注意: 当前使用友道翻译API",
            "友道免费API限制: 每小时1000次请求",
            "大型MOD可能需要分批处理",
            "=" * 70
        ])
        
        print("\n" + "\n".join(report))

# ===== 用户配置区 =====
# 从DeepL改为友道翻译API配置
YOUDAO_APP_KEY = "YOUR_YOUDAO_APP_KEY"  # 替换为你的友道应用ID
YOUDAO_APP_SECRET = "YOUR_YOUDAO_APP_SECRET"  # 替换为你的友道应用密钥
MOD_DIRECTORY = r"E:\gtxx4\localisation"  # 替换为mod本地化文件夹路径
MAX_WORKERS = 4  # 并发线程数，根据电脑性能调整(4-8)
# ======================

if __name__ == "__main__":
    print("=" * 70)
    print("HOI4 Mod终极汉化工具 v3.1 (友道API版)")
    print("=" * 70)
    
    # 配置检查
    if YOUDAO_APP_KEY == "YOUR_YOUDAO_APP_KEY" or YOUDAO_APP_SECRET == "YOUR_YOUDAO_APP_SECRET" or MOD_DIRECTORY == "FULL_PATH_TO_YOUR_MOD_LOCALIZATION":
        print("配置错误: 请先修改脚本中的配置信息!")
        print("1. 打开本脚本文件")
        print("2. 修改顶部的YOUDAO_APP_KEY, YOUDAO_APP_SECRET和MOD_DIRECTORY")
        print("3. 保存后重新运行")
        input("\n按Enter键退出...")
        sys.exit()
    
    # 路径验证
    if not os.path.exists(MOD_DIRECTORY):
        print(f"路径错误: {MOD_DIRECTORY} 不存在")
        print("请检查路径是否正确")
        input("\n按Enter键退出...")
        sys.exit()
    
    # 实例化并运行
    try:
        translator = HOI4UltimateTranslator(
            app_key=YOUDAO_APP_KEY,
            app_secret=YOUDAO_APP_SECRET,
            max_workers=MAX_WORKERS
        )
        translator.process_directory(MOD_DIRECTORY)
    except Exception as e:
        print(f"\n致命错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("\n按Enter键退出程序...")