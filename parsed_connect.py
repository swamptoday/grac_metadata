import pandas as pd

parsed_1 = "parsed_data_1.csv"
parsed_2 = "parsed_data_2.csv"
parsed_3 = "parsed_data_3.csv"
old_grac = "GRAC_Metadata_Authors.xlsx"

parsed_data_1 = pd.read_csv(parsed_1)
parsed_data_2 = pd.read_csv(parsed_2)
parsed_data_3 = pd.read_csv(parsed_3)
old_data = pd.read_excel(old_grac)

parsed_data = pd.concat([parsed_data_1, parsed_data_2, parsed_data_3])
parsed_data.to_csv('parsed_data.csv', index=False)


merged_data = pd.merge(old_data, parsed_data, on="Автор", how="left", suffixes=('_old', '_new'))

columns_to_fill = ["Рік народження", "Місце народження (населений пункт)", "Район", "Регіон1", "Стать", "Рідна мова"]
for column in columns_to_fill:
    old_column = f"{column}_old"
    new_column = f"{column}_new"
    
    if old_column in merged_data.columns and new_column in merged_data.columns:
        merged_data[column] = merged_data[old_column].combine_first(merged_data[new_column])
    elif new_column in merged_data.columns:
        merged_data[column] = merged_data[new_column]
    else:
        merged_data[column] = merged_data[old_column]

merged_data["Рік смерті"] = merged_data["Рік смерті"]
merged_data["Повне ім'я"] = merged_data["Повне ім'я"]
merged_data["URL"] = merged_data["URL"]

merged_data = merged_data[[col for col in merged_data.columns if not col.endswith(('_old', '_new'))]]

merged_data.to_excel("updated_data.xlsx", index=False)

print("Дані успішно оновлено та збережено в updated_data.xlsx!")