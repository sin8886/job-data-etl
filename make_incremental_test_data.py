import pandas as pd
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

SOURCE_FILE = BASE_DIR / "data" / "raw" / "DataAnalyst.csv"
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "DataAnalyst_test.csv"

# 读取原始数据
df = pd.read_csv(SOURCE_FILE)

print(f"Original rows: {len(df)}")

# 复制最后一条记录
new_row = df.iloc[-1].copy()

# ========= 修改业务键 =========
# Business Key:
# Company Name + Job Title + Location
#
# 至少修改其中一个字段，
# Incremental Filter 才会认为这是新数据。

new_row["Job Title"] = "Senior Data Analyst (Incremental Test)"

# 如果想测试其它情况，也可以改下面这些字段
# new_row["Company Name"] = "OpenAI"
# new_row["Location"] = "Auckland"

# 添加到最后
df = pd.concat(
    [df, pd.DataFrame([new_row])],
    ignore_index=True,
)

# 保存测试文件
df.to_csv(OUTPUT_FILE, index=False)

print(f"New rows: {len(df)}")
print(f"Saved to: {OUTPUT_FILE}")
print()
print("Incremental test data generated successfully.")
