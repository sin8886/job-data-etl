from pathlib import Path

import pandas as pd

# Project root directory.
BASE_DIR = Path(__file__).parent

SOURCE_FILE = BASE_DIR / "data" / "raw" / "DataAnalyst.csv"
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "DataAnalyst_test.csv"

# Read the raw data.
df = pd.read_csv(SOURCE_FILE)

print(f"Original rows: {len(df)}")

# Copy the last record.
new_row = df.iloc[-1].copy()

# ========= Modify the business key =========
# Business Key:
# Company Name + Job Title + Location
#
# Change at least one field so the incremental filter treats the row as new.

new_row["Job Title"] = "Senior Data Analyst (Day18 Retry Failure Test)"

# Modify the following fields to test other scenarios.
# new_row["Company Name"] = "OpenAI"
# new_row["Location"] = "Auckland"

# Append the new record.
df = pd.concat(
    [df, pd.DataFrame([new_row])],
    ignore_index=True,
)

# Save the test input file.
df.to_csv(OUTPUT_FILE, index=False)

print(f"New rows: {len(df)}")
print(f"Saved to: {OUTPUT_FILE}")
print()
print("Incremental test data generated successfully.")
