import pandas as pd
import re
from collections import Counter

# ===================== 全局路径配置（统一修改这里） =====================
# 原始评论数据文件
INPUT_REVIEW_FILE = r"E:\2026\4月\Jeans亚马逊评论数据_20260421.xlsx"
# 关键词库文件（原voc.py中的tree文件）
KEYWORD_FILE = r"E:\2026\4月\Jeans评论短语频次统计.xlsx"
# 最终合并输出文件
OUTPUT_MERGED_FILE = r"E:\2026\4月\Jeans评论_含身高体重_词频标签.xlsx"

# ===================== 1. 身高体重提取函数 =====================
def extract_height_weight(text):
    """
    从文本中提取身高（英尺-英寸）和体重（磅）
    返回：(身高字符串, 体重数值)
    """
    # 统一转小写，方便匹配
    text = str(text).lower().strip()
    
    # -------------------- 提取身高 --------------------
    height = None
    # 规则1：匹配 5’8”、5’9、5'8、5'9" 格式（最常见）
    pattern1 = r'(\d{1})[’\'`]\s*(\d{1,2})["”]?'
    match1 = re.search(pattern1, text)
    # 规则2：匹配 5 feet 9 inches、5 ft 9 in 格式
    pattern2 = r'(\d{1})\s*(feet|ft)\s*(\d{1,2})\s*(inches|in|")?'
    match2 = re.search(pattern2, text)
    # 规则3：匹配 height is 53 这类纯英寸数值（53英寸≈4'5"）
    pattern3 = r'height\s*is\s*(\d{2,3})'
    match3 = re.search(pattern3, text)
    
    if match1:
        feet = match1.group(1)
        inches = match1.group(2)
        # 验证合理范围（4-7英尺，0-11英寸）
        if 4 <= int(feet) <=7 and 0 <= int(inches) <=11:
            height = f"{feet}'{inches}\""
    elif match2:
        feet = match2.group(1)
        inches = match2.group(3)
        if 4 <= int(feet) <=7 and 0 <= int(inches) <=11:
            height = f"{feet}'{inches}\""
    elif match3:
        total_inches = int(match3.group(1))
        # 转换为英尺-英寸（1英尺=12英寸）
        if 48 <= total_inches <= 84:  # 4英尺(48) - 7英尺(84)
            feet = total_inches // 12
            inches = total_inches % 12
            height = f"{feet}'{inches}\""
    
    # -------------------- 提取体重 --------------------
    weight = None
    # 规则1：匹配 weight is 155、i weigh 155 格式
    pattern_weight1 = r'(weight\s*is|weigh)\s*(\d{2,3})'
    # 规则2：匹配 155 pounds、155lbs、155 lb 格式
    pattern_weight2 = r'(\d{2,3})\s*(pounds|lbs|lb)'
    
    match_w1 = re.search(pattern_weight1, text)
    match_w2 = re.search(pattern_weight2, text)
    
    if match_w1:
        weight_val = int(match_w1.group(2))
        if 80 <= weight_val <= 300:  # 合理体重范围（磅）
            weight = weight_val
    elif match_w2:
        weight_val = int(match_w2.group(1))
        if 80 <= weight_val <= 300:
            weight = weight_val
    
    return height, weight

# ===================== 2. 词频统计 + 标签匹配函数（原voc.py逻辑） =====================
def process_voc_and_matching(df):
    """
    处理词频统计和关键词匹配（原voc.py完整逻辑）
    返回：处理后的df、词频统计df、关键词库df
    """
    # 合并 title 和 content 英文文本（空值处理）
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["content"] = df["content"].fillna("").astype(str).str.strip()
    df["merged_text_voc"] = df["title"] + " " + df["content"]

    # 全文分词 + 全局词频统计
    def english_tokenize(text):
        words = re.findall(r"[a-zA-Z]+", text.lower())
        return [word for word in words if len(word) >= 2]

    df["single_words_list"] = df["merged_text_voc"].apply(english_tokenize)

    # 汇总词频
    all_total_words = []
    for word_list in df["single_words_list"]:
        all_total_words.extend(word_list)
    word_freq_result = Counter(all_total_words)

    # 控制台打印全局词频 Top50
    print("=" * 60)
    print("【全部文本全局词频统计 TOP 50】")
    print("=" * 60)
    for word, count in word_freq_result.most_common(50):
        print(f"{word} : {count}")

    # 读取关键词库 + 智能匹配
    tree_df = pd.read_excel(KEYWORD_FILE, usecols=[0])
    # 预处理关键词（修复核心错误：先选列，再处理字符串）
    # 1. 选中A列（Series），去空
    tree_series = tree_df.iloc[:, 0].dropna()
    # 2. 对Series做字符串处理（astype+strip）
    tree_series_clean = tree_series.astype(str).str.strip()
    # 3. 转为列表（过滤空字符串）
    keyword_all = [k for k in tree_series_clean.tolist() if k]
    # 长短语优先匹配
    keyword_all.sort(key=lambda x: len(x), reverse=True)

    # 匹配函数
    def match_phrase_and_word(full_text):
        text_low = full_text.lower()
        matched_list = []
        for kw in keyword_all:
            if kw in text_low:
                matched_list.append(kw)
        unique_matched = list(dict.fromkeys(matched_list))
        return ", ".join(unique_matched)

    df["matched_labels"] = df["merged_text_voc"].apply(match_phrase_and_word)

    # 整理词频统计结果
    word_freq_df = pd.DataFrame(word_freq_result.most_common(), columns=["单词", "出现频次"])
    word_freq_df["排名"] = range(1, len(word_freq_df) + 1)
    word_freq_df = word_freq_df[["排名", "单词", "出现频次"]]

    # 整理关键词库（修复核心错误：基于Series重建DataFrame）
    tree_df_clean = pd.DataFrame({"关键词库": tree_series_clean})

    # 删除临时列（避免重复）
    df = df.drop(columns=["merged_text_voc"], errors="ignore")
    
    return df, word_freq_df, tree_df_clean

# ===================== 3. 主流程：整合所有逻辑 =====================
def main():
    # 步骤1：读取原始评论数据
    print("🔍 读取原始评论数据...")
    df = pd.read_excel(INPUT_REVIEW_FILE)
    # 校验必要列
    if "title" not in df.columns or "content" not in df.columns:
        raise ValueError("原始表格缺少 title 或 content 列，请检查文件！")
    total_comments = len(df)
    print(f"✅ 成功读取 {total_comments} 条评论数据")

    # 步骤2：提取身高体重
    print("\n🔍 开始提取身高体重数据...")
    # 合并title+content（扩大提取范围）
    df["merged_text_hw"] = df["title"].astype(str) + " " + df["content"].astype(str)
    # 批量提取
    df[["extracted_height", "extracted_weight_lbs"]] = df["merged_text_hw"].apply(
        lambda x: pd.Series(extract_height_weight(x))
    )
    # 删除临时列
    df = df.drop(columns=["merged_text_hw"], errors="ignore")

    # 步骤3：统计身高体重提取结果
    has_height = df["extracted_height"].notna().sum()
    has_weight = df["extracted_weight_lbs"].notna().sum()
    has_both = df[(df["extracted_height"].notna()) & (df["extracted_weight_lbs"].notna())].shape[0]
    print("="*60)
    print("✅ 身高体重提取完成！")
    print(f"总评论数：{total_comments}")
    print(f"提取到身高的评论数：{has_height} ({has_height/total_comments:.2%})")
    print(f"提取到体重的评论数：{has_weight} ({has_weight/total_comments:.2%})")
    print(f"同时提取到身高+体重的评论数：{has_both}")
    print("="*60)

    # 步骤4：处理词频统计和标签匹配（原voc.py逻辑）
    print("\n🔍 开始处理词频统计和标签匹配...")
    df, word_freq_df, tree_df_clean = process_voc_and_matching(df)

    # 步骤5：导出所有结果到同一个Excel（多Sheet）
    print("\n🔍 导出合并文件...")
    with pd.ExcelWriter(OUTPUT_MERGED_FILE, engine="openpyxl") as writer:
        # Sheet1：原始评论 + 身高体重 + 标签匹配
        df.to_excel(writer, sheet_name="评论_身高体重_标签", index=False)
        # Sheet2：全局词频统计
        word_freq_df.to_excel(writer, sheet_name="全局词频统计", index=False)
        # Sheet3：关键词库
        tree_df_clean.to_excel(writer, sheet_name="评论关键词库", index=False)

    # 步骤6：展示前10条提取结果示例
    print("\n📌 前10条身高体重提取结果示例：")
    sample = df[["title", "content", "extracted_height", "extracted_weight_lbs"]].head(10)
    for idx, row in sample.iterrows():
        print(f"评论{idx+1} | 身高：{row['extracted_height']} | 体重：{row['extracted_weight_lbs']} lbs")

    # 最终提示
    print("\n" + "="*80)
    print("✅ 所有处理完成！合并文件保存路径：")
    print(OUTPUT_MERGED_FILE)
    print("\n📋 文件包含Sheet说明：")
    print("1. 评论_身高体重_标签：原始评论 + 提取的身高体重 + 匹配的关键词标签")
    print("2. 全局词频统计：所有评论的单词词频（带排名）")
    print("3. 评论关键词库：去空后的原始关键词列表")
    print("="*80)

if __name__ == "__main__":
    main()
