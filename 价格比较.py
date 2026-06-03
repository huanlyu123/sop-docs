
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ====================== 只需改这里 ======================
EXCEL_PATH = "C:/Users/admin/Downloads/scooter.xlsx"
FILE_2024 = "C:/Users/admin/Downloads/scooter2024.xlsx"
FILE_2025 = "C:/Users/admin/Downloads/scooter.xlsx"

SHEET_NAME = "Product Performance"
ASIN_COLUMN = "Asin"
PRICE_COLUMN = "Avg. Price"
REVENUE_COLUMN = "Revenue"
# =======================================================

file_base = os.path.splitext(os.path.basename(EXCEL_PATH))[0]
# ---------------------- 读取数据 ----------------------
df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df = df.dropna(subset=[ASIN_COLUMN, PRICE_COLUMN, REVENUE_COLUMN]).copy()

df[PRICE_COLUMN] = pd.to_numeric(df[PRICE_COLUMN], errors="coerce")
df[REVENUE_COLUMN] = pd.to_numeric(df[REVENUE_COLUMN], errors="coerce")
df = df[(df[PRICE_COLUMN] > 0) & (df[REVENUE_COLUMN] >= 0)].copy()

# ====================== 1. 5元区间分布图（判断正态） ======================
print("\n" + "="*80)
print("📊 第一步：5元区间 ASIN 分布（判断是否正态）")
print("="*80)

max_price = df[PRICE_COLUMN].max()
bins_50 = np.arange(0, max_price + 50, 50)
df["50元区间"] = pd.cut(df[PRICE_COLUMN], bins=bins_50, right=False)
asin_dist = df["50元区间"].value_counts().sort_index()

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.figure(figsize=(18, 6))
asin_dist.plot(kind="bar", color="#a1c9f4", alpha=0.9)
plt.title("5元价格区间 ASIN 数量分布", fontsize=16, fontweight="bold")
plt.ylabel("ASIN 数量")
plt.xticks(rotation=60, fontsize=10)
plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(f"50元区间_ASIN分布-{file_base}.png", dpi=300)
plt.show()

# ====================== 2. 选择分档模式：自动 / 手动 ======================
print("\n✅ 请查看上图！")
mode = input("是否符合正态分布？(y=自动分档 / n=我手动定义价格区间)：").strip().lower()

labels = ["低价位", "中低价位", "中价位", "中高价位", "高价位"]

if mode == "y":
    print("\n📏 使用【自动正态分档】")
    quantiles = [0.0, 0.05, 0.275, 0.725, 0.95, 1.0]
    breaks = df[PRICE_COLUMN].quantile(quantiles).round(2).tolist()
else:
    print("\n📝 使用【手动自定义分档】")
    print("请输入 5 个档位的【4个分界价格】，用英文逗号隔开")
    print("例子：10,20,35,60 → 0~10,10~20,20~35,35~60,60~最高")
    
    while True:
        try:
            user_input = input("输入分界点：")
            custom_breaks = [float(x.strip()) for x in user_input.split(",")]
            if len(custom_breaks) == 4:
                breaks = [0] + custom_breaks + [round(df[PRICE_COLUMN].max(), 2)]
                break
            else:
                print("❌ 必须输入 4 个数字！")
        except:
            print("❌ 格式错误，重新输入！")

intervals = [f"{breaks[i]}~{breaks[i+1]}元" for i in range(len(breaks)-1)]

df["价位段"] = pd.cut(df[PRICE_COLUMN], bins=breaks, labels=labels, include_lowest=True)
df["价格区间"] = pd.cut(df[PRICE_COLUMN], bins=breaks, labels=intervals, include_lowest=True)

# ====================== 3. 统计结果 ======================
result = df.groupby(["价位段", "价格区间"], observed=True).agg(
    ASIN数量=(ASIN_COLUMN, "count"),
    总GMV=(REVENUE_COLUMN, "sum")
).reset_index()

result["产品占比(%)"] = (result["ASIN数量"] / result["ASIN数量"].sum() * 100).round(1)
result["GMV占比(%)"] = (result["总GMV"] / result["总GMV"].sum() * 100).round(1)

print("\n" + "="*90)
print("📊 最终 5 档位统计结果")
print("="*90)
print(result.to_string(index=False))
x_labels = [f"{a}\n({b})" for a,b in zip(result["价位段"], result["价格区间"])]

# ====================== 4. GMV 分布图 ======================
plt.figure(figsize=(14,7))
bars = plt.bar(x_labels, result["总GMV"], color="#4a90e2", alpha=0.88)
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x()+bar.get_width()/2, h+h*0.01, f"{h:,.0f}", ha="center")
plt.title("各价位段 GMV 分布", fontsize=16)
plt.ylabel("GMV")
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"价位段GMV-{file_base}.png", dpi=300)
plt.show()

# ====================== 5. ASIN 数量分布图 ======================
plt.figure(figsize=(14,8), dpi=120)
colors = ["#66c2a5","#8da0cb","#fc8d62","#e78ac3","#a6d854"]
bars = plt.bar(x_labels, result["ASIN数量"], color=colors, edgecolor="white", linewidth=1.5, alpha=0.95)
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x()+bar.get_width()/2, h+max(result["ASIN数量"])*0.01, f"{int(h)}", ha="center", fontweight="bold")
plt.title("各价位段 ASIN 数量分布", fontsize=18, fontweight="bold")
plt.ylabel("ASIN数量")
plt.gca().spines[["top","right"]].set_visible(False)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig("ASIN数量分布.png", dpi=300)
#plt.show()

# ---------------------- 6. 2024→2025 价格变化分析 ----------------------
print("\n" + "="*80)
print("📊 2024→2025 各价位段价格变化分析")
print("="*80)

df24 = pd.read_excel(FILE_2024, sheet_name=SHEET_NAME)[[ASIN_COLUMN, PRICE_COLUMN]].rename(columns={PRICE_COLUMN:"2024价格"})
df25 = pd.read_excel(FILE_2025, sheet_name=SHEET_NAME)[[ASIN_COLUMN, PRICE_COLUMN]].rename(columns={PRICE_COLUMN:"2025价格"})

merged = pd.merge(df24, df25, on=ASIN_COLUMN, how="inner")
merged["差价"] = merged["2025价格"] - merged["2024价格"]
merged["变化类型"] = np.where(merged["差价"]>0.01,"上涨",
                         np.where(merged["差价"]<-0.01,"下跌","不变"))

asin_to_level = df[[ASIN_COLUMN, "价位段", "价格区间"]].drop_duplicates()
merged = merged.merge(asin_to_level, on=ASIN_COLUMN, how="inner")

group = merged.groupby(["价位段","价格区间","变化类型"], observed=True).size().reset_index(name="ASIN数量")
pivot = group.pivot_table(index=["价位段","价格区间"], columns="变化类型", values="ASIN数量", fill_value=0).reset_index()

# ====================== ✅ 超级修复：确保三列都存在 ======================
for col in ["上涨", "下跌", "不变"]:
    if col not in pivot.columns:
        pivot[col] = 0

pivot["合计"] = pivot["上涨"] + pivot["下跌"] + pivot["不变"]
pivot["上涨占比(%)"] = (pivot["上涨"]/pivot["合计"]*100).round(1)
pivot["下跌占比(%)"] = (pivot["下跌"]/pivot["合计"]*100).round(1)
pivot["不变占比(%)"] = (pivot["不变"]/pivot["合计"]*100).round(1)

print(pivot.to_string(index=False))

# ====================== 画图 ======================
plt.figure(figsize=(16,8))
x = np.arange(len(pivot))
w = 0.25
plt.bar(x-w, pivot["上涨"], w, label="上涨", color="#e74c3c")
plt.bar(x,   pivot["下跌"], w, label="下跌", color="#2ecc71")
plt.bar(x+w, pivot["不变"], w, label="不变", color="#f39c12")

xlabels = [f"{a}\n({b})" for a,b in zip(pivot["价位段"], pivot["价格区间"])]
plt.xticks(x, xlabels, fontsize=11)
plt.title("2024→2025 各价位段价格变化分布", fontsize=16, fontweight="bold")
plt.ylabel("ASIN数量")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.gca().spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"2024-2025价位段价格变化-{file_base}.png", dpi=300)
#plt.show()

# 导出
result.to_excel(f"5档位GMV_ASIN统计-{file_base}.xlsx", index=False)
pivot.to_excel(f"2024-2025价格变化按价位段统计-{file_base}.xlsx", index=False)

print("\n✅ 全部完成！所有图表 + Excel 已保存")
