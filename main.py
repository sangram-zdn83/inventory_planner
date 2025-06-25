import os
import json

import streamlit as st
import pandas as pd

from modules.data_loader import load_master_data, load_input_data
from modules.preprocessing import preprocess_master_data
from modules.optimization import build_products, optimize_production, build_output
from modules.scheduling import build_parallel_production_timeline
from modules.utils import create_product_mappings


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

    # Get timeline and errors
    timeline, errors = build_parallel_production_timeline(
        products,
        hours,
        product_number_to_product_description,
        input_list,
        max_shifts_per_day=1,
    )

    # Convert date objects to ISO strings for JSON serialization
    for item in timeline:
        for key in ["Start Date", "End Date", "Due Date"]:
            if key in item and hasattr(item[key], "isoformat"):
                item[key] = item[key].isoformat()

    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Write timeline to a JSON file
    with open(os.path.join(output_dir, "production_timeline.json"), "w") as f:
        json.dump(timeline, f, indent=2)

    # Write errors to a JSON file if any
    if errors:
        with open(os.path.join(output_dir, "error.json"), "w") as f:
            json.dump(errors, f, indent=2)

    st.title("Production Planning Optimization")
    st.subheader("Production Plan Results")
    st.write(pd.DataFrame(timeline))

    if errors:
        st.error("Some products could not be scheduled. See error.json for details.")


if __name__ == "__main__":
    main()
