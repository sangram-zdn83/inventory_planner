from math import ceil, floor
from datetime import timedelta, date


def build_parallel_production_timeline(
    products,
    hours,
    product_number_to_product_description,
    input_list,
    max_shifts_per_day=3,
):
    desc_to_due = {item["Product Description"]: item["Due Date"] for item in input_list}
    desc_to_asked_qty = {
        item["Product Description"]: item["Quantity"] for item in input_list
    }
    timeline = []
    errors = []
    tomorrow = date.today() + timedelta(days=1)
    for p in products:
        h = hours[p].varValue
        h = ceil(h)
        staff = products[p]["staff"]
        shifts_needed = ceil(h / 8)
        days_needed = ceil(shifts_needed / max_shifts_per_day)
        prod_desc = product_number_to_product_description[p]
        due_date = desc_to_due[prod_desc].date()  # Convert to datetime.date
        start_date = date.today() + timedelta(days=1)  # tomorrow
        end_date = start_date + timedelta(days=days_needed - 1)
        if end_date > due_date:
            errors.append(
                f"Scheduling not possible for '{prod_desc}': end date {end_date} exceeds due date {due_date}"
            )
            continue
        asked_quantity = desc_to_asked_qty[prod_desc]
        planned_quantity = floor(products[p]["productivity"] * h)
        attainment = f"{round(planned_quantity / asked_quantity, 2) * 100}%"
        timeline.append(
            {
                "Product Description": prod_desc,
                "Start Date": start_date,
                "End Date": end_date,
                "Planned Hours": h,
                "Staff": staff,
                "Shifts Needed": shifts_needed,
                "Days Needed": days_needed,
                "Due Date": due_date,
                "Asked Quantity": asked_quantity,
                "Planned Quantity": planned_quantity,
                "Attainment": attainment,
            }
        )
    return timeline, errors
