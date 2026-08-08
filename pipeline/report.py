import time


def generate_report(df, path="report.md"):

    content = f"""
# Pipeline Report

generated_at:
{time.strftime("%Y-%m-%d %H:%M:%S")}

rows:
{len(df)}

"""

    with open(path, "w", encoding="utf-8") as f:

        f.write(content)
