import pandas as pd


def preprocess_master_data(df):
    df = df[
        [
            "Product #",
            "Product Description",
            "Qty/Labour Hr              (calculated Qty/Shift/8/Staff)",
            "Staff",
        ]
    ]
    df.columns = df.columns.str.replace(
        "Qty/Labour Hr              (calculated Qty/Shift/8/Staff)",
        "Qty/Labour Hr (calculated Qty/Shift/8/Staff)",
    )
    df["Product #"] = df["Product #"].astype(str)
    df["Product Description"] = df["Product Description"].astype(str)
    df["Qty/Labour Hr (calculated Qty/Shift/8/Staff)"] = pd.to_numeric(
        df["Qty/Labour Hr (calculated Qty/Shift/8/Staff)"], errors="coerce"
    )
    df["Staff"] = pd.to_numeric(df["Staff"], errors="coerce")
    df["Product Description"] = df["Product Description"].str.strip()
    df = df.dropna()
    return df
