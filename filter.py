import pandas as pd

# input_file_1 = "wikipedia_results/wikipedia_results_1_500.csv"
# input_file_2 = "wikipedia_results/wikipedia_results_501_1000.csv"
# input_file_3 = "wikipedia_results/wikipedia_results_1001_5000.csv"
# df_1 = pd.read_csv(input_file_1)
# df_2 = pd.read_csv(input_file_2)
# df_3 = pd.read_csv(input_file_3)

# df = pd.concat([df_1, df_2, df_3])

input_file = "wikipedia_results/wikipedia_results_15001_26728.csv"
df = pd.read_csv(input_file)
df_filtered = df[df['URL'].notnull()]
df_cleaned = df_filtered.drop_duplicates(subset=['URL'])

df_cleaned.to_csv("authors_urls_3.csv", index=False)