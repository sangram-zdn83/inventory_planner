import json
from math import ceil, floor

import pandas as pd
import pulp
import streamlit as st


def load_master_data(file_path):
    return pd.read_excel(file_path, sheet_name="MASTER DATA")


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


def create_product_mappings(df):
    product_description_to_product_number = df.set_index("Product Description")[
        "Product #"
    ].to_dict()
    product_number_to_product_description = df.set_index("Product #")[
        "Product Description"
    ].to_dict()
    return product_description_to_product_number, product_number_to_product_description


def load_input_data(input_csv):
    input_df = pd.read_csv(input_csv)
    input_list = []
    for _, row in input_df.iterrows():
        input_list.append(
            {
                "Product Description": row["Product Description"],
                "Quantity": row["Quantity"],
            }
        )
    return input_list


def build_products(input_list, df, product_description_to_product_number):
    products = {}
    for item in input_list:
        product_description = item["Product Description"]
        quantity = item["Quantity"]

        if product_description in product_description_to_product_number:
            product_number = product_description_to_product_number[product_description]
            qty_per_shift = df.loc[
                df["Product #"] == product_number,
                "Qty/Labour Hr (calculated Qty/Shift/8/Staff)",
            ].values[0]
            staff = df.loc[df["Product #"] == product_number, "Staff"].values[0]

            products[product_number] = {
                "po_qty": quantity,
                "productivity": qty_per_shift,
                "staff": staff,
            }
        else:
            raise Exception(
                f"Product Description '{product_description}' not found in master data."
            )
    return products


def optimize_production(products, total_hours):
    model = pulp.LpProblem("Production_Planning", pulp.LpMaximize)
    hours = {
        p: pulp.LpVariable(f"h_{p}", lowBound=0, cat="Continuous") for p in products
    }
    model += (
        pulp.lpSum([products[p]["productivity"] * hours[p] for p in products]),
        "Total_Production",
    )
    model += (
        pulp.lpSum([hours[p] * products[p]["staff"] for p in products]) <= total_hours,
        "Total_Labor_Hours",
    )
    for p in products:
        model += (
            products[p]["productivity"] * hours[p] <= products[p]["po_qty"],
            f"Max_PO_Qty_{p}",
        )
    model.solve()
    return hours


def build_output(products, hours, product_number_to_product_description):
    output = []
    for p in products:
        h = hours[p].varValue
        h = ceil(h)
        q = products[p]["productivity"] * h
        q = floor(q)
        asked_quantity = products[p]["po_qty"]
        output.append(
            {
                "Product Description": product_number_to_product_description[p],
                "Status": "Planned",
                "Planned Hours": h,
                "Asked Quantity": asked_quantity,
                "Planned Quantity": q,
                "Estimated Attainment": f"{round(q / asked_quantity, 2) * 100}%",
            }
        )
    return output


def main():
    file_path = "data/Daily Operating & Production Order Entry Report.xlsx"
    input_csv = "data/sample.csv"
    total_hours = 100000

    df = load_master_data(file_path)
    df = preprocess_master_data(df)
    product_description_to_product_number, product_number_to_product_description = (
        create_product_mappings(df)
    )
    input_list = load_input_data(input_csv)
    products = build_products(input_list, df, product_description_to_product_number)

    if products:
        hours = optimize_production(products, total_hours)
        output = build_output(products, hours, product_number_to_product_description)

    st.title("Production Planning Optimization")
    st.subheader("Production Plan Results")
    st.write(pd.DataFrame(output))


if __name__ == "__main__":
    main()
