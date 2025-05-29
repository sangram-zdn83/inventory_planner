import json
from math import ceil

import pandas as pd
import pulp
import streamlit as st

file_path = "data/Daily Operating & Production Order Entry Report.xlsx"

sheet_names = pd.ExcelFile(file_path).sheet_names

# read MASTER DATA and the following columns = Product #, Qty/Shift, Staff
df = pd.read_excel(file_path, sheet_name="MASTER DATA")

# filter rows where Status is "Active"
df = df[df["Status"] == "Active"]

# select relevant columns
df = df[
    [
        "Product #",
        "Product Description",
        "Qty/hr             (calculate Qty/Shift/8)",
        "Staff",
    ]
]

df = df.dropna()

# create Product Description to Proect # mapping
product_description_to_product_number = df.set_index("Product Description")[
    "Product #"
].to_dict()

# create a mapping of Product # to Product Description
product_number_to_product_description = df.set_index("Product #")[
    "Product Description"
].to_dict()

# Input: Product Description, Quantity
input = [
    {
        "Product Description": "Yogurt Club Pack Costco",
        "Quantity": 41063,
    },
    {
        "Product Description": "QUAKER  Yogurt Club Pack Retail 30ct",
        "Quantity": 4000,
    },
    {
        "Product Description": "Family Pack 18ct Maple & Brown Sugar",
        "Quantity": 3600,
    },
    {
        "Product Description": "IQO  66ct Club Pack - new mix",
        "Quantity": 35000,
    },
    {
        "Product Description": "Food Service Chewy  Choc. Chip",
        "Quantity": 5400,
    },
    {
        "Product Description": "FRITO LAY 54 CT VARIETY ",
        "Quantity": 26880,
    },
    {
        "Product Description": "Yogourt Chocolate Variety",
        "Quantity": 3000,
    },
    {
        "Product Description": "Agro. 2L Natrel Plus 2% Van Case",
        "Quantity": 1000,
    },
    {
        "Product Description": "Sea Salt Caramel Mousse",
        "Quantity": 64,
    },
]

# Define product data like below from input
# {
#     "Product_A": {"po_qty": 10000, "productivity": 500, "staff": 10},
#     "Product_B": {"po_qty": 8000, "productivity": 400, "staff": 8},
# }

products = {}
output = []
for item in input:
    product_description = item["Product Description"]
    quantity = item["Quantity"]

    if product_description in product_description_to_product_number:
        product_number = product_description_to_product_number[product_description]
        qty_per_shift = df.loc[
            df["Product #"] == product_number,
            "Qty/hr             (calculate Qty/Shift/8)",
        ].values[0]
        staff = df.loc[df["Product #"] == product_number, "Staff"].values[0]

        products[product_number] = {
            "po_qty": quantity,
            "productivity": qty_per_shift,
            "staff": staff,
        }
    else:
        print(f"Product description '{product_description}' not found in MASTER DATA.")
        output.append(
            {
                "Product Description": product_description,
                "Status": "Error: Product not found in MASTER DATA",
                "Planned Hours": None,
                "Asked Quantity": quantity,
                "Planned Quantity": None,
                "Estimated Overproduction": None,
            }
        )

# print("+++++++++++")
# print(json.dumps(products, indent=4))
# print("+++++++++++")

# Total available staff-hours in the week (e.g. 5 days × 8 hrs/day × 10 staff)
total_hours = 5000

# Define the LP problem
model = pulp.LpProblem("Production_Planning", pulp.LpMaximize)

# Decision variables: hours allocated to each product
hours = {p: pulp.LpVariable(f"h_{p}", lowBound=0, cat="Continuous") for p in products}

# Objective: Maximize total production
model += (
    pulp.lpSum([products[p]["productivity"] * hours[p] for p in products]),
    "Total_Production",
)

# Constraint: Total labor-hours used <= available
model += (
    pulp.lpSum([hours[p] * products[p]["staff"] for p in products]) <= total_hours,
    "Total_Labor_Hours",
)

# Constraint: Cannot produce more than PO quantity
for p in products:
    model += (
        products[p]["productivity"] * hours[p] <= products[p]["po_qty"],
        f"Max_PO_Qty_{p}",
    )

# Solve the model
model.solve()

print("+++++++++++")
print("SOLUTION:")
print("+++++++++++")

# Output the results
for p in products:
    h = hours[p].varValue
    h = ceil(h)
    q = products[p]["productivity"] * h
    print(
        f"{product_number_to_product_description[p]}: Allocate {h:.2f} hours → Produce {q:.0f} units"
    )

    asked_quantity = products[p]["po_qty"]
    output.append(
        {
            "Product Description": product_number_to_product_description[p],
            "Status": "Planned",
            "Planned Hours": h,
            "Asked Quantity": asked_quantity,
            "Planned Quantity": q,
            "Estimated Overproduction": f"{round((q - asked_quantity) / asked_quantity, 2) * 100}%",
        }
    )

st.title("Production Planning Optimization")

# Display the results in a Streamlit table
st.subheader("Production Plan Results")
st.write(pd.DataFrame(output))
