from math import ceil, floor

import pulp


def build_products(input_list, df, product_description_to_product_number):
    products = {}
    for item in input_list:
        # pdb.set_trace()
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
