# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 文字處理器

修復 OCR 結果中的空格和格式問題。
"""

import re
from functools import lru_cache

# 可選依賴：英文分詞
try:
    import wordninja
    HAS_WORDNINJA = True
except ImportError:
    HAS_WORDNINJA = False


# ========== 常數定義 ==========

# OCR 錯誤合併修正
MERGE_TERMS = {
    # MEMS 術語
    'Poly MUMPs': 'PolyMUMPs',
    'Poly MUMPS': 'PolyMUMPs',
    'SOIMUMP s': 'SOIMUMPs',
    'SOI MUMPs': 'SOIMUMPs',
    'Metal MUMPs': 'MetalMUMPs',
    'MEMS cAP': 'MEMScAP',
    'MEMSc AP': 'MEMScAP',
    'MEMSC AP': 'MEMScAP',
    'MEMSc ap': 'MEMScAP',
    'MEMSProcesses': 'MEMS Processes',
    'MEMSprocesses': 'MEMS processes',
    
    # 符號空格修復
    '2025©': '2025 ©',
    '2024©': '2024 ©',
    '2023©': '2023 ©',
    '2022©': '2022 ©',
    '©Chiu': '© Chiu',
    ',Yi': ', Yi',
    ',Fall': ', Fall',
    'Fall,2': 'Fall, 2',
    
    # 數字後黏連修復
    '81runs': '81 runs',
    '82runs': '82 runs',
    '9thrun': '9th run',
    
    # 常見黏連詞
    'micromachiningby': 'micromachining by',
    'micromachiningfor': 'micromachining for',
    
    # 版本號 OCR 錯誤修正（數字 1 被丟失）
    '.v0.pdf': '.v10.pdf',
    '.v0.doc': '.v10.doc',
    '.v0.docx': '.v10.docx',
    '_v0.pdf': '_v10.pdf',
    '_v0.doc': '_v10.doc',
    'dr.v0': 'dr.v10',
    '_v0_': '_v10_',
    '-v0-': '-v10-',
    # v1x 系列
    '.v1.pdf': '.v11.pdf' if False else '.v1.pdf',  # 保持不變，只修復確定錯誤
    '.v2.pdf': '.v12.pdf' if False else '.v2.pdf',
    
    # 常見數字 OCR 錯誤
    ' l ': ' 1 ',  # 小寫 L 誤識為 1
    ' O ': ' 0 ',  # 大寫 O 誤識為 0
    ' ll ': ' 11 ',
    
    # 檔案名稱修正
    '.pdi': '.pdf',
    '.PD F': '.PDF',
    '. pdf': '.pdf',
    
    # 日期格式修正
    '202 5': '2025',
    '202 4': '2024',
    '1 9': '19',
    '2 0': '20',
    
    # 單位修正
    'u m': 'μm',
    'u M': 'μM',
}

# 受保護的專業術語（不應被拆分）
PROTECTED_TERMS = {
    'MUMPs', 'PolyMUMPs', 'SOIMUMPs', 'MetalMUMPs',
    'MEMScAP', 'MEMSCAP', 'MEMSProcesses', 'MEMSdevices',
    'micromachining', 'Micromachining', 'MICROMACHINING',
    'FoundryService', 'CMOS', 'MEMS', 'OCR', 'PDF',
    'PaddleOCR', 'PowerPoint', 'JavaScript', 'TypeScript',
    'GitHub', 'LinkedIn', 'YouTube', 'Facebook',
    'iPhone', 'iPad', 'macOS', 'iOS', 'WiFi',
    'TM', 'PhD', 'CEO', 'CTO', 'CFO',
    '0th', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th',
    '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th',
    '20th', '21st', '22nd', '23rd', '24th', '25th', '30th', '40th', '50th',
    'v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10',
}

# 常見黏連詞修復
COMMON_SPLITS = {
    'Aprogram': 'A program',
    'aprogram': 'a program',
    'Theprogram': 'The program',
    'theprogram': 'the program',
    'programoffered': 'program offered',
    'isdesigned': 'is designed',
    'wasestablished': 'was established',
    'hasbeen': 'has been',
    'canbe': 'can be',
    'willbe': 'will be',
    'tobe': 'to be',
    'forthe': 'for the',
    'tothe': 'to the',
    'ofthe': 'of the',
    'inthe': 'in the',
    'onthe': 'on the',
    'bythe': 'by the',
    'andthe': 'and the',
    'isthe': 'is the',
    'asthe': 'as the',
    'withthe': 'with the',
    'Designof': 'Design of',
    'designof': 'design of',
    'micromachiningby': 'micromachining by',
    'isused': 'is used',
    'areused': 'are used',
    'canbeused': 'can be used',
    'providescustomers': 'provides customers',
    'includesthe': 'includes the',
    'suchas': 'such as',
    'aswellas': 'as well as',
    'inorder': 'in order',
    'orderto': 'order to',
    'dueto': 'due to',
    'byvarious': 'by various',
    'forvarious': 'for various',
    'withcost': 'with cost',
    'tofabricate': 'to fabricate',
    'todesign': 'to design',
    'toannounce': 'to announce',
}

# 常見連字符詞
COMMON_HYPHENATED = {
    'wellestablished': 'well-established',
    'costeffective': 'cost-effective',
    'highperformance': 'high-performance',
    'lowpower': 'low-power',
    'stateoftheart': 'state-of-the-art',
    'realtime': 'real-time',
    'onchip': 'on-chip',
    'offchip': 'off-chip',
    'multiuser': 'multi-user',
    'Multi User': 'Multi-User',
    'waferlevel': 'wafer-level',
    'Wafer Level': 'Wafer-Level',
}


@lru_cache(maxsize=10000)
def fix_english_spacing(text: str, use_wordninja: bool = True) -> str:
    """
    修復英文 OCR 結果中的空格問題（帶快取優化）
    
    策略：
    1. 保護專業術語不被拆分
    2. CamelCase 分詞：FoundryService → Foundry Service
    3. wordninja 智能分詞（可選）
    4. 修復連字符詞
    5. 數字前後空格
    
    快取優化：
    - 相同文字直接返回快取結果
    - 最多快取 10000 個結果
    - 大幅提升重複文字處理速度
    
    Args:
        text: 輸入文字
        use_wordninja: 是否使用 wordninja 智能分詞
        
    Returns:
        修復後的文字
    """
    if not text:
        return text
    
    result = text
    
    # 0. 合併被 OCR 錯誤分詞的術語
    for wrong, correct in MERGE_TERMS.items():
        result = result.replace(wrong, correct)
    
    # 用佔位符保護專業術語（按長度排序，長的先處理）
    protected_map = {}
    sorted_terms = sorted(PROTECTED_TERMS, key=len, reverse=True)
    for i, term in enumerate(sorted_terms):
        if term in result:
            placeholder = f"__PROT_{i}__"
            protected_map[placeholder] = term
            result = result.replace(term, placeholder)
    
    # 1. CamelCase 分詞
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    result = re.sub(r'([a-z])(__PROT_)', r'\1 \2', result)
    
    # 2. 大寫序列後接小寫
    result = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1 \2', result)
    
    # 3. 數字和字母之間空格
    result = re.sub(
        r'(\d)([a-zA-Z])',
        lambda m: m.group(0) if m.group(2).lower() in ['t','s','n','r','v'] else m.group(1) + ' ' + m.group(2),
        result
    )
    result = re.sub(r'([a-uw-z])(\d)', r'\1 \2', result)
    
    # 4. 標點符號後空格
    result = re.sub(r'\.(\d)', r'. \1', result)
    result = re.sub(r'\.([A-Z])', r'. \1', result)
    result = re.sub(r',([A-Za-z])', r', \1', result)
    
    # 5. 括號前後空格
    result = re.sub(r'([a-zA-Z])\(', r'\1 (', result)
    result = re.sub(r'\)([a-zA-Z])', r') \1', result)
    
    # 5.1 常見黏連詞
    for wrong, correct in COMMON_SPLITS.items():
        result = result.replace(wrong, correct)
    
    # 6. 連字符詞
    for wrong, correct in COMMON_HYPHENATED.items():
        result = re.sub(wrong, correct, result, flags=re.IGNORECASE)
    
    # 7. wordninja 智能分詞
    if use_wordninja and HAS_WORDNINJA:
        def split_long_words(match):
            word = match.group(0)
            if len(word) > 10:
                parts = wordninja.split(word.lower())
                if len(parts) > 1:
                    if word[0].isupper():
                        parts[0] = parts[0].capitalize()
                    return ' '.join(parts)
            return word
        
        result = re.sub(r'\b[A-Za-z]{11,}\b', split_long_words, result)
    
    # 恢復專業術語
    for placeholder, term in protected_map.items():
        result = result.replace(placeholder, term)
    
    # 8. 清理多餘空格
    result = re.sub(r' +', ' ', result)
    
    return result
