
import pandas as pd
import re
from deep_translator import GoogleTranslator
import warnings
warnings.filterwarnings('ignore')
import os

# ===================== 全局配置（按需修改） =====================
# 文件路径
SEARCH_WORDS_FILE = r"E:/2026/4月/wideleg_jeans_cst.xlsx"
CST_TREE_FILE = r"E:\2026\4月\cst_tree.xlsx"
OUTPUT_FILE = r"E:\2026\4月\对比结果_未匹配单词1.xlsx"

# 列配置
SEARCH_COL = 0  # 搜索词A列
CST_TREE_COL = 2  # cst_tree C列

# 匹配模式：True=包含匹配（推荐，适配短语），False=精准匹配（原逻辑）
MATCH_MODE = True  # 重点：改为True解决短语匹配问题

# ===================== 辅助函数 =====================
def clean_text_func(text):
    """清洗文本：去空、转字符串、去首尾空格、统一小写（修改函数名避免冲突）"""
    if pd.isna(text):
        return ""
    return str(text).strip().lower()

def translate_to_zh(text):
    """英文转中文，处理异常"""
    if not text or text.strip() == "":
        return ""
    try:
        return GoogleTranslator(source='auto', target='zh-CN').translate(text)
    except Exception as e:
        print(f"⚠️ 翻译失败（{text}）：{str(e)[:50]}")
        return "翻译失败"

def is_matched(search_text, cst_text_list):
    """
    匹配逻辑：
    - 包含匹配：搜索词是任意一个cst文本的子串
    - 精准匹配：搜索词与任意一个cst文本完全相等
    """
    if not search_text:
        return False, ""
    
    for cst_text in cst_text_list:
        if not cst_text:
            continue
        # 包含匹配
        if MATCH_MODE and search_text in cst_text:
            return True, "包含匹配（搜索词是cst短语的子串）"
        # 精准匹配
        elif not MATCH_MODE and search_text == cst_text:
            return True, "精准匹配"
    return False, "未匹配"

# ===================== 主逻辑 =====================
def main():
    try:
        # 1. 校验文件
        if not os.path.exists(SEARCH_WORDS_FILE):
            raise FileNotFoundError(f"搜索词文件不存在：{SEARCH_WORDS_FILE}")
        if not os.path.exists(CST_TREE_FILE):
            raise FileNotFoundError(f"cst_tree文件不存在：{CST_TREE_FILE}")

        # 2. 读取数据
        print("🔍 读取文件数据...")
        df_search = pd.read_excel(SEARCH_WORDS_FILE, usecols=[SEARCH_COL])
        df_search.columns = ["原始英文"]
        df_cst = pd.read_excel(CST_TREE_FILE, usecols=[CST_TREE_COL])
        df_cst.columns = ["cst_c列文本"]

        # 3. 清洗数据（调用重命名后的清洗函数）
        print("🧹 清洗数据...")
        # 清洗搜索词
        df_search["清洗后英文"] = df_search["原始英文"].apply(clean_text_func)
        # 清洗cst_tree并去重（减少匹配次数）
        df_cst["清洗后文本"] = df_cst["cst_c列文本"].apply(clean_text_func)
        cst_clean_list = df_cst["清洗后文本"].drop_duplicates().tolist()
        cst_clean_list = [x for x in cst_clean_list if x != ""]  # 过滤空值

        # 4. 批量匹配（修改变量名，避免和函数重名）
        print("🔎 开始匹配（模式：{}）...".format("包含匹配" if MATCH_MODE else "精准匹配"))
        match_results = []
        for idx, row in df_search.iterrows():
            original_text = row["原始英文"]
            cleaned_text = row["清洗后英文"]  # 变量名改为cleaned_text，避免冲突
            
            # 跳过空值
            if not cleaned_text:
                continue
            
            # 执行匹配（传入修改后的变量名）
            matched, match_type = is_matched(cleaned_text, cst_clean_list)
            match_results.append({
                "原始英文": original_text,
                "清洗后英文": cleaned_text,
                "匹配状态": match_type if matched else "未在cst_tree.xlsx的C列中找到",
                "是否匹配": matched
            })

        # 转为DataFrame
        df_match = pd.DataFrame(match_results)

        # 5. 筛选未匹配内容 + 去重
        df_unmatched = df_match[~df_match["是否匹配"]].copy()
        df_unmatched = df_unmatched.drop_duplicates(subset=["清洗后英文"])  # 去重
        df_unmatched = df_unmatched.reset_index(drop=True)

        # 6. 翻译未匹配内容
        if len(df_unmatched) > 0:
            print("🌐 翻译未匹配内容...")
            df_unmatched["中文翻译"] = df_unmatched["原始英文"].apply(translate_to_zh)
        else:
            print("✅ 所有搜索词均已匹配，无需翻译！")
            df_unmatched["中文翻译"] = ""

        # 7. 整理输出结果
        df_result = df_unmatched[["原始英文", "匹配状态", "中文翻译"]]

        # 8. 导出结果
        df_result.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ 处理完成！结果已导出至：{OUTPUT_FILE}")

        # 9. 统计信息
        total_search = len(df_match)
        total_matched = df_match["是否匹配"].sum()
        total_unmatched = len(df_unmatched)
        print(f"\n📊 统计结果：")
        print(f"- 搜索词.xlsx A列有效文本总数：{total_search}")
        print(f"- 匹配成功数：{total_matched}（{total_matched/total_search:.2%}）")
        print(f"- 未匹配数：{total_unmatched}（{total_unmatched/total_search:.2%}）")
        print(f"- 匹配模式：{('包含匹配（适配短语）' if MATCH_MODE else '精准匹配')}")

    except FileNotFoundError as e:
        print(f"\n❌ 错误：{e}")
        print("💡 请检查文件路径是否正确！")
    except Exception as e:
        print(f"\n❌ 运行出错：{type(e).__name__} - {e}")

if __name__ == "__main__":
    main()
