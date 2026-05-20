import openpyxl
import random

# Function to read products from the Excel file
def read_products_from_excel(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    products = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        product_id = row[0]
        if product_id is None:
            break
        
        products[product_id] = {
            'name': row[1],
            'weight': row[2],
            'frozen': row[3],
            'fresh': row[4],
            'meat': row[5],
            'fish': row[6],
            'locations': [int(x) for x in str(row[7]).split(',')],
            'icon': row[8]
        }
    
    #Remove items with None id from the dictionary
    products = {k: v for k, v in products.items() if k is not None}

    return products

def read_products_from_json(file_path_1, file_path_2):
    products = {}
    import json
    with open(file_path_1, 'r') as f:
        products_df = json.load(f)
    with open(file_path_2, 'r') as f:
        locations_df = json.load(f)
    for product in products_df:
        product_id = product['unique_id']
        products[product_id] = {
            'name': product['title'],
            'frozen': 1 if product['sub_category1'] == "Congelados" else 0,
            'fresh': 1 if product['sub_category1'] == "Charcutaria&Queijos" else 0,
            'meat': 1 if product['sub_category1'] == 'Talho' else 0,
            'fish': 1 if product['sub_category2'] == 'Peixaria' else 0,
            'locations': [int(locations_df[product_id])] if product_id in locations_df else [random.randint(0, 108)],
            'image_url': product['image_url'],
            'icon': '🍎'
        }
    return products


#test the function
#file_path_1 = 'SIGA_Product_Feed_9.json'
#file_path_2 = 'products_location.json'
#products = read_products_from_json(file_path_1, file_path_2)
#print(products)
