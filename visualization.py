import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = r"D:\桌面\DE\data\clean\jobs_chunk_clean.csv"

OUTPUT_FILE = "top10_companies.png"


def plot_top_companies(input_file, output_file):

    # Read the cleaned data.
    df = pd.read_csv(input_file)

    # Count job postings by company.
    company_counts = df["Company Name"].value_counts().head(10)

    # Create the chart.
    plt.figure(figsize=(10, 6))

    company_counts.sort_values().plot.barh()

    plt.title("Top 10 Companies by Job Count")

    plt.xlabel("Number of Jobs")

    plt.ylabel("Company")

    plt.tight_layout()

    plt.savefig(output_file, dpi=300)

    plt.close()

    print(f"Visualization saved: {output_file}")


if __name__ == "__main__":

    plot_top_companies(INPUT_FILE, OUTPUT_FILE)
