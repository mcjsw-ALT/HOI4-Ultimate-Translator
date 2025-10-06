import os
import re
import requests
import shutil
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class HOI4UltimateTranslator:
    def __init__(self, api_key, source_lang="EN", target_lang="ZH", max_workers=4):
        """
        HOI4 Mod终极汉化工具 v4.0 - 专业钢铁雄心4版
        专为HOI4 MOD优化，支持军事术语保护、变量保护和上下文感知翻译
        """
        self.api_key = api_key
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_workers = max_workers
        self.endpoint = "https://api-free.deepl.com/v2/translate"
        
        # 增强的智能正则表达式系统（HOI4专用）
        self.text_regex = re.compile(r'^(\s*[^\s:]+(?::\d+)?\s+)(".*?")$', re.MULTILINE)
        self.var_regex = re.compile(
            r'(\$[a-zA-Z0-9_]+?\$|'  # 标准变量 $VARIABLE$
            r'§[HhYyGg]|'            # 颜色代码 §H, §Y等
            r'§[a-zA-Z0-9_]+|'       # 其他§开头的代码
            r'%[a-zA-Z0-9_]+%|'      # %变量%
            r'[A-Z]{3,}_[A-Z0-9_]+)' # 国家代码+变量名 GER_INVASION_FORCE
        )
        self.key_extract_regex = re.compile(r'^\s*([^\s:]+)')
        
        # 统计系统
        self.processed_count = 0
        self.error_count = 0
        self.format_fixes = 0
        self.reference_replacements = 0
        self.protected_count = 0
        self.quality_log = []  # 翻译质量日志
        
        # 智能缓存系统
        self.translation_map = {}
        self.global_translation_map = {}
        self.protected_terms = self.load_protected_terms()
        
        # 加载基础术语表（HOI4专用）
        self.glossary = self.load_glossary()
        hoi4_glossary = self.load_hoi4_glossary()
        # 合并术语表（HOI4基础术语优先）
        for term, translation in hoi4_glossary.items():
            if term not in self.glossary:
                self.glossary[term] = translation
        
        # 智能排序系统
        self.file_priority = {
            "l_english.yml": 0,
            "l_simp_chinese.yml": 100,
            "focuses.yml": 10,
            "events.yml": 20,
            "ideas.yml": 30,
            "decisions.yml": 40
        }
    
    def load_protected_terms(self):
        """加载HOI4专有名词保护列表"""
        hoi4_terms = [
            # 国家与阵营
            "Axis", "Allies", "Comintern", "Faction", "Reich", "Reichskommissariat",
            "Entente", "Alliance", "Pact", "Coalition", "Central Powers",
            
            # 军事术语
            "Division", "Battalion", "Brigade", "Garrison", "Manpower", "Equipment",
            "Organization", "Combat Width", "Breakthrough", "Soft Attack", "Hard Attack",
            "Armor", "Piercing", "Air Superiority", "CAS", "Strategic Bombing", "Encryption",
            "Decryption", "Recon", "Entrenchment", "Supply", "Logistics", "Attrition",
            "Reinforcement", "Deployment", "Mobilization", "Conscription", "Reserves",
            
            # 游戏机制
            "Focus", "National Focus", "Decision", "Event", "Idea", "Doctrine", "Spy",
            "Stability", "War Support", "Compliance", "Resistance", "Collaboration",
            "Ideology", "Democracy", "Fascism", "Communism", "Neutrality", 
            "Production", "Research", "Technology", "Factory", "Dockyard", "Resource",
            "Trade", "Economy", "Diplomacy", "Politics", "Propaganda",
            
            # 特定装备
            "Panzer", "Tiger", "Panther", "Sherman", "Zero", "Spitfire", "Bf 109", "IL-2",
            "Bismarck", "Yamato", "Enterprise", "T-34", "KV-1", "IS-2", "P-51", "Fw 190",
            
            # 历史人物
            "Hitler", "Stalin", "Churchill", "Roosevelt", "Mussolini", "Hirohito",
            "Zhukov", "Rommel", "Patton", "Montgomery", "Eisenhower", "Yamamoto",
            "De Gaulle", "Tito", "Chiang", "Mao", "Tojo", "Himmler", "Goering",
            
            # 地名和战役
            "Barbarossa", "Normandy", "Stalingrad", "Berlin", "Moscow", "London", "Paris",
            "Pearl Harbor", "Midway", "Guadalcanal", "El Alamein", "Dunkirk", "Kursk",
            "Ardennes", "Okinawa", "Iwo Jima", "Warsaw", "Kiev", "Leningrad", "Volga",
            
            # 历史事件和概念
            "Blitzkrieg", "Anschluss", "Appeasement", "Manhattan Project", "Enigma",
            "Holocaust", "Final Solution", "Kamikaze", "Valkyrie", "Operation", 
            "Luftwaffe", "Wehrmacht", "Red Army", "SS", "Gestapo", "NKVD", "RAF", "USAAF",
            
            # 国家代码
            "GER", "SOV", "USA", "ENG", "FRA", "ITA", "JAP", "POL", "CHI", "SPR", "SPA"
        ]
        
        try:
            if os.path.exists("protected_terms.json"):
                with open("protected_terms.json", "r", encoding="utf-8") as f:
                    user_terms = json.load(f)
                    return list(set(hoi4_terms + user_terms))  # 合并系统与用户术语
        except:
            pass
        return hoi4_terms
    
    def load_hoi4_glossary(self):
        """加载HOI4基础术语表"""
        hoi4_glossary = {
            "army_experience": "陆军经验",
            "navy_experience": "海军经验",
            "air_experience": "空军经验",
            "command_power": "指挥点数",
            "political_power": "政治点数",
            "stability": "稳定度",
            "war_support": "战争支持度",
            "division_template": "师模板",
            "combat_width": "战斗宽度",
            "front_line": "前线",
            "encirclement": "包围",
            "supply": "补给",
            "logistics": "后勤",
            "conscription_law": "征兵法案",
            "economy_law": "经济法案",
            "trade_law": "贸易法案",
            "war_economy": "战时经济",
            "partial_mobilization": "部分动员",
            "service_by_requirement": "义务兵役制",
            "all_volunteers": "全志愿兵役制",
            "scraping_the_barrel": "榨干他们",
            "war_propaganda": "战争宣传",
            "ideological_crusade": "意识形态圣战",
            "desperate_defense": "绝望防御",
            "blitzkrieg": "闪电战",
            "grand_battleplan": "大规模计划",
            "superior_firepower": "优势火力",
            "mass_assault": "人海战术",
            "battle_plan": "作战计划",
            "planning_bonus": "计划加成",
            "entrenchment": "战壕",
            "reinforce_rate": "增援率",
            "attack": "攻击",
            "defense": "防御",
            "breakthrough": "突破",
            "armor": "装甲",
            "piercing": "穿甲",
            "hardness": "硬度",
            "air_superiority": "空中优势",
            "close_air_support": "近距离空中支援",
            "strategic_bomber": "战略轰炸机",
            "nuclear_bomb": "核弹",
            "resistance": "抵抗运动",
            "compliance": "顺从度",
            "collaboration_government": "合作政府",
            "collaborationist": "合作者"
        }
        return hoi4_glossary
    
    def load_glossary(self):
        """加载用户术语表"""
        try:
            if os.path.exists("translation_glossary.json"):
                with open("translation_glossary.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_glossary(self):
        """保存自动生成的术语表"""
        if not self.glossary:
            return
            
        try:
            with open("translation_glossary.json", "w", encoding="utf-8") as f:
                json.dump(self.glossary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"\n无法保存术语表: {str(e)}")
    
    def _replace_special_content(self, text):
        """保护游戏变量、专有名词和术语表条目"""
        replacements = {}
        placeholder_template = "__HOI4_VAR_{}__"
        
        # 保护术语表条目
        for term, translation in self.glossary.items():
            if term in text:
                text = text.replace(term, f"__GLOSSARY_{term}__")
        
        # 保护专有名词
        for term in self.protected_terms:
            if term in text:
                self.protected_count += 1
                text = text.replace(term, f"__PROTECTED_{term}__")
        
        # 保护游戏变量
        def replace_match(match):
            var = match.group(0)
            placeholder = placeholder_template.format(len(replacements))
            replacements[placeholder] = var
            return placeholder
        
        processed_text = self.var_regex.sub(replace_match, text)
        return processed_text, replacements
    
    def _restore_special_content(self, text, replacements):
        """恢复所有保护内容"""
        # 恢复游戏变量
        for placeholder, var in replacements.items():
            text = text.replace(placeholder, var)
        
        # 恢复专有名词
        for term in self.protected_terms:
            text = text.replace(f"__PROTECTED_{term}__", term)
        
        # 恢复术语表条目
        for term in self.glossary:
            text = text.replace(f"__GLOSSARY_{term}__", self.glossary[term])
        
        # HOI4专用后处理修正
        text = self._hoi4_post_process(text)
        return text
    
    def _hoi4_post_process(self, text):
        """HOI4专用后处理修正"""
        # 修正常见误译
        corrections = {
            "德国": "德国",  # 防止错误的变体
            "俄罗斯": "苏联",
            "苏维埃": "苏联",
            "坦克": "坦克",
            "装甲的": "装甲",
            "分裂": "师",    # division误译修正
            "焦点": "国策",  # focus误译修正
            "支持战争": "战争支持度",
            "战争支持": "战争支持度",
            "稳定": "稳定度",
            "稳定性": "稳定度",
            "战斗计划": "作战计划",
            "计划奖金": "计划加成",
            "突破": "突破",
            "装甲": "装甲",
            "刺穿": "穿甲",
            "空中霸权": "空中优势",
            "近距离空中支援": "近距离空中支援",
            "战略轰炸机": "战略轰炸机",
            "原子弹": "核弹",
            "反抗": "抵抗运动",
            "依从性": "顺从度",
            "合作政府": "合作政府",
            "合作者": "合作者"
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # 确保军事单位格式正确
        text = re.sub(r'(\d+)(?:st|nd|rd|th)?\s?(步兵师|装甲师|骑兵师|山地师|陆战队|伞兵师|摩托化师|机械化师)', r'\1\2', text)
        
        # 确保国家代码后加冒号
        text = re.sub(r'^([A-Z]{3})\s', r'\1: ', text, flags=re.MULTILINE)
        
        return text
    
    def _fix_format_issues(self, line):
        """自动修复格式问题"""
        # 修复缺失的:0
        if re.match(r'^\s*[a-zA-Z0-9_]+:?\s+"', line) and ':0' not in line:
            self.format_fixes += 1
            return line.replace('"', ':0 "', 1)
        
        # 修复不正确的引号
        if re.match(r'^\s*[a-zA-Z0-9_]+:\d+\s+[^"]', line) and '"' not in line:
            if ':' in line:
                parts = line.split(':', 1)
                return f'{parts[0]}:"{parts[1].strip()}"'
        
        return line
    
    def _translate_text(self, text):
        """智能翻译引擎（HOI4优化版）"""
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
        
        # HOI4上下文提示
        context_hints = ""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["event", "option", "desc"]):
            context_hints = "[军事事件]"
        elif "focus" in text_lower:
            context_hints = "[国策]"
        elif any(term in text_lower for term in ["decision", "allowed", "effect"]):
            context_hints = "[决议]"
        elif any(term in text_lower for term in ["division", "battalion", "army", "navy", "air"]):
            context_hints = "[军事单位]"
        elif any(term in text_lower for term in ["idea", "trait", "spirit"]):
            context_hints = "[国家精神]"
        elif any(term in text_lower for term in ["technology", "research", "doctrine"]):
            context_hints = "[科技]"
        
        # 添加到翻译文本前
        if context_hints:
            protected_text = f"{context_hints} {protected_text}"
        
        # 准备API请求
        headers = {"Authorization": f"DeepL-Auth-Key {self.api_key}"}
        data = {
            "text": protected_text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "preserve_formatting": "1",
            "tag_handling": "xml"
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, data=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            translated_text = result['translations'][0]['text']
            
            # 恢复特殊内容
            final_text = self._restore_special_content(translated_text, replacements)
            
            # 添加到术语表
            if key and key not in self.glossary:
                self.glossary[key] = final_text
            
            # 质量评估（简单版）
            if "[" in original_text and "]" in original_text:
                orig_vars = set(re.findall(r'$$([^$$]+)\]', original_text))
                trans_vars = set(re.findall(r'$$([^$$]+)\]', final_text))
                if orig_vars != trans_vars:
                    self.quality_log.append({
                        "key": key,
                        "original": original_text,
                        "translated": final_text,
                        "issue": "变量丢失或变化"
                    })
            
            return final_text
        
        except Exception as e:
            print(f"\n翻译出错: {str(e)}")
            self.error_count += 1
            return original_text
    
    def _process_references(self, content):
        """增强版引用处理系统（支持HOI4多级引用）"""
        # 查找所有引用模式
        ref_matches = list(set(re.findall(r'(\$[^\s$]+\$)', content)))
        
        # 多级解析（最多3级）
        for _ in range(3):
            replacements_made = 0
            for ref in ref_matches:
                ref_key = ref.strip('$')
                
                if ref_key in self.global_translation_map:
                    translated_value = self.global_translation_map[ref_key]
                    # 只替换完整匹配的变量
                    new_content = re.sub(rf'\${ref_key}\$', translated_value, content)
                    if new_content != content:
                        content = new_content
                        self.reference_replacements += 1
                        replacements_made += 1
            
            # 如果没有新的替换，提前退出
            if replacements_made == 0:
                break
        
        return content
    
    def _process_yaml_file(self, file_path):
        """高级文件处理引擎（HOI4优化）"""
        try:
            # 重置本地缓存
            self.translation_map = {}
            local_fixes = 0
            
            # 创建备份
            backup_path = f"{file_path}.backup"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 预处理：识别并标记需要翻译的行
            lines = content.split('\n')
            translated_lines = []
            
            # 第一轮：收集所有键值对
            key_value_map = {}
            for line in lines:
                if match := self.text_regex.match(line):
                    key_match = self.key_extract_regex.match(line)
                    if key_match:
                        key = key_match.group(1).strip()
                        key_value_map[key] = line
            
            # 第二轮：按优先级排序
            sorted_keys = sorted(key_value_map.keys(), key=lambda k: self.file_priority.get(k, 50))
            
            # 第三轮：翻译并记录
            for key in sorted_keys:
                line = key_value_map[key]
                translated_line = self._translate_text(line)
                translated_lines.append(translated_line)
                
                # 记录到全局缓存
                key_match = self.key_extract_regex.match(translated_line)
                if key_match:
                    key_name = key_match.group(1).strip()
                    self.global_translation_map[key_name] = translated_line
            
            # 添加非翻译行
            for line in lines:
                if not self.text_regex.match(line) and line not in key_value_map.values():
                    translated_lines.append(line)
            
            # 合并处理后的内容
            translated_content = '\n'.join(translated_lines)
            
            # 处理引用
            translated_content = self._process_references(translated_content)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            self.processed_count += 1
            return self.format_fixes - local_fixes
        
        except Exception as e:
            print(f"\n处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
            self.error_count += 1
            return 0
    
    def process_directory(self, directory_path):
        """多线程目录处理系统（优先处理核心文件）"""
        # 收集所有yml文件
        yaml_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.yml'):
                    full_path = os.path.join(root, file)
                    # 优先级排序
                    priority = self.file_priority.get(file, 50)
                    yaml_files.append((priority, full_path))
        
        # 按优先级排序
        yaml_files.sort(key=lambda x: x[0])
        sorted_files = [f[1] for f in yaml_files]
        total_files = len(sorted_files)
        
        if not total_files:
            print("未找到YML文件! 请检查路径是否正确")
            return
        
        print(f"找到 {total_files} 个本地化文件，按优先级排序处理中...")
        
        # 多线程处理
        total_fixes = 0
        with tqdm(total=total_files, desc="汉化进度", unit="file") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._process_yaml_file, file): file for file in sorted_files}
                
                for future in as_completed(futures):
                    fixes = future.result()
                    total_fixes += fixes
                    pbar.update(1)
                    pbar.set_postfix({
                        "修复": total_fixes,
                        "引用": self.reference_replacements,
                        "保护": self.protected_count
                    })
        
        # 保存术语表
        self.save_glossary()
        
        # 生成终极报告
        self.generate_report(total_files, total_fixes)
    
    def generate_report(self, total_files, total_fixes):
        """生成终极质量报告（HOI4专用版）"""
        report = [
            "=" * 70,
            "HOI4 MOD 汉化终极报告",
            "=" * 70,
            f"处理文件总数: {total_files}",
            f"成功处理文件: {self.processed_count}",
            f"错误文件数: {self.error_count}",
            "-" * 70,
            f"自动格式修复: {total_fixes} 处",
            f"变量引用替换: {self.reference_replacements} 处",
            f"专有名词保护: {self.protected_count} 处",
            f"术语表条目: {len(self.glossary)} 个",
            "=" * 70,
            "翻译质量评估:"
        ]
        
        # 质量评估
        if self.error_count == 0 and self.processed_count == total_files:
            report.append("★ 完美 - 所有文件处理成功，无错误")
        elif self.error_count / total_files < 0.05:
            report.append("☆ 优秀 - 少数文件存在小问题")
        else:
            report.append("⚠ 一般 - 存在较多问题，建议检查")
        
        # 添加质量日志信息
        if self.quality_log:
            report.append(f"-" * 70)
            report.append(f"翻译质量警告: {len(self.quality_log)} 处潜在问题")
            report.append(f"已保存到: translation_quality_log.json")
            
            # 保存详细日志
            with open("translation_quality_log.json", "w", encoding="utf-8") as f:
                json.dump(self.quality_log, f, ensure_ascii=False, indent=2)
        
        report.extend([
            "=" * 70,
            "下一步操作指南:",
            "1. 在.mod文件中添加: language = \"l_simp_chinese\"",
            "2. 在游戏中测试汉化效果",
            "3. 检查术语表(translation_glossary.json)，优化特定术语",
            "4. 扩展保护列表(protected_terms.json)，添加更多专有名词",
            "5. 查看翻译质量日志(translation_quality_log.json)，修正问题条目",
            "=" * 70,
            "高级提示:",
            "- 重新运行本工具会自动使用术语表，确保一致性",
            "- 优先处理核心文件：焦点、事件、决议和军事单位文件",
            "- 对于大型MOD，可分多次运行以避免API限制",
            "- 使用引用替换计数检查变量引用是否完整",
            "=" * 70
        ])
        
        print("\n" + "\n".join(report))

# ===== 用户配置区 =====
DEEPL_API_KEY = "54e388ea-56f6-4b96-a052-a65d118e71a5:fx"  # 替换为你的DeepL API密钥
MOD_DIRECTORY = r"E:\gtxx4\localisation"  # 替换为mod本地化文件夹路径
MAX_WORKERS = 4 # 并发线程数，根据电脑性能调整(4-8)
# ======================

if __name__ == "__main__":
    print("=" * 70)
    print("HOI470)
    print("HOI4 Mod终极汉化工具 v4.0 - 专业钢铁雄心4版")
    print("=" * 70)
    
    # 配置检查
    if DEEPL_API_KEY == "YOUR_API_KEY_HERE" or MOD_DIRECTORY == "FULL_PATH_TO_YOUR_MOD_LOCALIZATION":
        print("配置错误: 请先修改脚本中的配置信息!")
        print("1. 打开本脚本文件")
        print("2. 修改顶部的DEEPL_API_KEY和MOD_DIRECTORY")
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
            api_key=DEEPL_API_KEY,
            max_workers=MAX_WORKERS
        )
        translator.process_directory(MOD_DIRECTORY)
    except Exception as e:
        print(f"\n致命错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("\n按Enter键退出程序...")