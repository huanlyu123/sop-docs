import pandas as pd
import re
from collections import Counter

# ===================== 1. 读取原始亚马逊评论数据 =====================
data_file = r"E:\2026\4月\Jeans亚马逊评论数据_20260421.xlsx"
df = pd.read_excel(data_file)

# 校验必要列
if "title" not in df.columns or "content" not in df.columns:
    raise ValueError("原始表格缺少 title 或 content 列，请检查文件！")

# ===================== 2. 合并 title 和 content 英文文本 =====================
# 空值统一转为空字符串，去除首尾空格（修复strip报错问题）
df["title"] = df["title"].fillna("").astype(str).str.strip()
df["content"] = df["content"].fillna("").astype(str).str.strip()
# 合并文本列
df["merged_text"] = df["title"] + " " + df["content"]

# ===================== 3. 全文分词 + 全局词频统计（所有文本汇总词频） =====================
# 英文分词函数（提取所有英文单词，小写，过滤单个字母无意义词）
def english_tokenize(text):
    # 提取所有英文单词
    words = re.findall(r"[a-zA-Z]+", text.lower())
    # 过滤长度小于2的无效词
    return [word for word in words if len(word) >= 2]

# 逐行分词存入新列
df["single_words_list"] = df["merged_text"].apply(english_tokenize)

# 汇总全部行所有单词，统计全局词频
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

# ===================== 4. 读取tree.xlsx关键词库（A列：单词+短语混合）+ 智能匹配 =====================
# 读取关键词文件，仅读取A列
tree_file = r"E:\2026\4月\Jeans评论短语频次统计.xlsx"
tree_df = pd.read_excel(tree_file, usecols=[0])

# 预处理所有关键词：去空、去首尾空格、统一小写
keyword_all = tree_df.iloc[:, 0].dropna().astype(str).str.strip().str.lower().tolist()
# 过滤空关键词
keyword_all = [k for k in keyword_all if k]

# 长短语优先匹配，避免短词覆盖
keyword_all.sort(key=lambda x: len(x), reverse=True)

# 逐行匹配函数：同时匹配短语 + 单词
def match_phrase_and_word(full_text):
    text_low = full_text.lower()
    matched_list = []
    for kw in keyword_all:
        if kw in text_low:
            matched_list.append(kw)
    # 去重并逗号分隔
    unique_matched = list(dict.fromkeys(matched_list))
    return ", ".join(unique_matched)

# 生成匹配结果列
df["matched_labels"] = df["merged_text"].apply(match_phrase_and_word)

# ===================== 5. 导出文件 =====================
output_save_path = r"E:\2026\4月\Jeans亚马逊评论数据_20260421_matchedlabel.xlsx"
df.to_excel(output_save_path, index=False)

print("\n" + "=" * 60)
print("✅ 处理完成！文件已保存：")
print(output_save_path)
print("匹配规则：支持单词+英文短语，长短语优先，自动去重，逗号分隔")
print("=" * 60)
