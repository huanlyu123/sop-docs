

# ===================== 全局配置 =====================
# 文件路径

import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import os
from nltk.stem import WordNetLemmatizer
import nltk

# 自动下载词形还原语料（首次运行触发）
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# ===================== 全局配置 =====================
# 文件路径
SEARCH_WORDS_FILE = r"E:\2026\4月\wideleg_jeans_cst.xlsx"    # 搜索词文件（A列，长文本）
CST_TREE_FILE = r"E:\2026\4月\cst_tree.xlsx"      # CST文件（C列，短语/单词库）
OUTPUT_FILE = r"E:\2026\4月\wideleg_jeans_cst_cstlabel.xlsx"  # 后缀_cstlabel

# 列配置
SEARCH_MAIN_COL = 0  # 用于匹配的搜索词列（A列）
CST_TREE_COL = 2     # CST取C列

# ===================== 核心工具函数 =====================
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    """清洗文本：去空、转字符串、去首尾空格、统一小写"""
    if pd.isna(text):
        return ""
    return str(text).strip().lower()

def normalize_plural(text):
    """词形归一化：转为单数（忽略单复数），支持短语"""
    if not text:
        return ""
    words = text.split()
    normalized_words = [lemmatizer.lemmatize(w, pos='n') for w in words]
    return " ".join(normalized_words)

def extract_matched_cst(search_long_text, cst_data):
    """
    核心逻辑：从搜索词（长文本）中提取所有匹配的CST文本（优先长CST词）
    规则：
    1. CST文本按长度降序（长词优先匹配）
    2. 忽略单复数（归一化后匹配）
    3. CST文本是搜索词的子串 → 提取该CST文本
    """
    matched_cst_list = []
    # 清洗+归一化搜索词（长文本）
    search_clean = clean_text(search_long_text)
    if not search_clean:
        return "无匹配"
    search_norm = normalize_plural(search_clean)
    
    # 遍历按长度降序的CST数据（优先匹配长CST词）
    for _, row in cst_data.iterrows():
        cst_original = row["原始文本"]    # CST原始文本（如high waist）
        cst_clean = row["清洗后文本"]    # CST清洗文本
        cst_norm = row["归一化文本"]     # CST归一化文本（忽略单复数）
        
        if not cst_clean:
            continue
        
        # 关键：CST归一化文本 是 搜索词归一化文本的子串 → 匹配成功
        if cst_norm in search_norm:
            # 避免重复添加
            if cst_original not in matched_cst_list:
                matched_cst_list.append(cst_original)
    
    # 用逗号分隔匹配结果，无匹配则显示"无匹配"
    return ", ".join(matched_cst_list) if matched_cst_list else "无匹配"

# ===================== 主执行逻辑 =====================
def main():
    try:
        # 1. 校验文件
        if not os.path.exists(SEARCH_WORDS_FILE):
            raise FileNotFoundError(f"搜索词文件不存在：{SEARCH_WORDS_FILE}")
        if not os.path.exists(CST_TREE_FILE):
            raise FileNotFoundError(f"CST文件不存在：{CST_TREE_FILE}")

        # 2. 读取数据（核心修改：读取搜索词的所有列，而非仅A列）
        print("🔍 读取文件数据（保留所有列）...")
        # 读取搜索词的全部列
        df_search = pd.read_excel(SEARCH_WORDS_FILE)
        # 确认用于匹配的列存在（A列，即第0列）
        search_main_col_name = df_search.columns[SEARCH_MAIN_COL]
        print(f"📌 用于匹配的搜索词列：{search_main_col_name}（A列）")
        
        # 读取CST数据（仅C列）
        df_cst = pd.read_excel(CST_TREE_FILE, usecols=[CST_TREE_COL])
        df_cst.columns = ["原始文本"]

        # 3. CST数据预处理：清洗+归一化+按长度降序排序（长词优先）
        print("🧹 预处理CST数据（清洗+归一化+长词排序）...")
        df_cst["清洗后文本"] = df_cst["原始文本"].apply(clean_text)
        df_cst["归一化文本"] = df_cst["清洗后文本"].apply(normalize_plural)
        df_cst["文本长度"] = df_cst["清洗后文本"].apply(lambda x: len(x) if x else 0)
        # 按长度降序+去重（避免重复匹配）
        df_cst_sorted = df_cst.sort_values(by="文本长度", ascending=False) \
                              .drop_duplicates(subset=["清洗后文本"]) \
                              .reset_index(drop=True)

        # 4. 批量匹配：新增matched_cst列（保留所有原有列）
        print("🔎 开始匹配（优先长CST词+忽略单复数）...")
        df_search["matched_cst"] = df_search[search_main_col_name].apply(
            lambda x: extract_matched_cst(x, df_cst_sorted)
        )

        # 5. 导出结果（保留所有列+新增matched_cst列，后缀_cstlabel）
        df_search.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ 匹配完成！结果已导出至：{OUTPUT_FILE}")
        print(f"📌 输出文件包含列：{list(df_search.columns)}")

        # 6. 统计信息
        total_search = len(df_search)
        matched_count = len(df_search[df_search["matched_cst"] != "无匹配"])
        print(f"\n📊 匹配统计：")
        print(f"- 搜索词总行数：{total_search}")
        print(f"- 匹配成功数：{matched_count}（{matched_count/total_search:.2%}）")
        print(f"- 无匹配数：{total_search - matched_count}（{(total_search - matched_count)/total_search:.2%}）")

    except FileNotFoundError as e:
        print(f"\n❌ 错误：{e}")
        print("💡 请检查文件路径是否正确！")
    except IndexError:
        print(f"\n❌ 错误：搜索词文件的A列不存在！请确认文件格式正确")
    except Exception as e:
        print(f"\n❌ 运行出错：{type(e).__name__} - {e}")

if __name__ == "__main__":
    main()
