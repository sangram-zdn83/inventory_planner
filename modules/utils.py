def create_product_mappings(df):
    product_description_to_product_number = df.set_index("Product Description")[
        "Product #"
    ].to_dict()
    product_number_to_product_description = df.set_index("Product #")[
        "Product Description"
    ].to_dict()
    return product_description_to_product_number, product_number_to_product_description
