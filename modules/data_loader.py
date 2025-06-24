import pandas as pd


def load_master_data(file_path):
    return pd.read_excel(file_path, sheet_name="MASTER DATA")


def load_input_data(input_csv):
    input_df = pd.read_csv(input_csv)
    input_list = []
    for _, row in input_df.iterrows():
        input_list.append(
            {
                "Product Description": row["Product Description"],
                "Quantity": row["Quantity"],
                "Due Date": pd.to_datetime(row["Due Date"]),
            }
        )
    return input_list
