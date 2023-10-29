from pymongo import MongoClient
from ean import ean
import os
import requests


# Connect to MongoDB
client = MongoClient(process.env.MONGODB_URL)

db = client["okayletsgo"]
collection = db["kjøh"]


#asdfasdasdf
def get_product(ean):
    url = f"https://kassal.app/api/v1/products/ean/{ean}"
    headers = {
        'Authorization': f'Bearer {process.env.KASSAL_BEARER_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    return prettify_product(response)

def prettify_product(response):
    response_json = response.json()
    stores = []

    for store in response_json['data']['products']:
        if store['store'] is None or store['current_price'] is None:
            continue

        stores.append({
            'storeName': store['store']['name'],
            'storePrice': store['current_price']['price']
        })

    stores.sort(key=lambda x: x['storePrice'])

    pretty_product = {
        'ean': response_json['data']['ean'],
        'productName': response_json['data']['products'][0]['name'],
        'stores': stores
    }

    return pretty_product

def update_product(product):
    try:  
        filter = {'ean': product['ean']}
        collection.update_one(filter, {'$set': product}, upsert=True)
        return {'status': 200}
    except Exception as error:
        return {'status': 500, 'body': error}
    

def update_db():
    for code in ean.values():
        product = get_product(code)
        update_product(product)
    return {'status': 200}

update_db()