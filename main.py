from pymongo import MongoClient
from dotenv.main import load_dotenv
from datetime import datetime, timedelta
from ean import ean
import os
import requests
import time
import json


load_dotenv()

client = MongoClient(os.environ.get("MONGO_URL"))

db = client["okayletsgo"]
collection = db["kjøh"]


def get_product(ean):
    url = f"https://kassal.app/api/v1/products/ean/{ean}"
    headers = {
        'Authorization': f'Bearer {os.environ.get("KASSAL_BEARER_TOKEN")}'
    }
    response = requests.get(url, headers=headers)
    test = json.dumps(response.json(), indent=4)

    return prettify_product(response)

def is_more_than_30_days_ago(date_string):
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    parsed_date = datetime.strptime(date_string, date_format)
    current_date = datetime.now()
    delta = current_date - parsed_date
    return delta > timedelta(days=30)

def prettify_product(response):
    response_json = response.json()
    stores = []
    description = None

    for store in response_json['data']['products']:

        if store['store'] is None:
            continue

        if is_more_than_30_days_ago(store['current_price']['date']):
            continue

        if store['description'] is not None:
            description = store['description']
            if description == '':
                description = None


        stores.append({
            'storeName': store['store']['name'],
            'storePrice': store['current_price']['price']
        })

        
    if len(stores) == 0:
            return None
    
    stores.sort(key=lambda x: x['storePrice'])

    pretty_product = {
        'ean': response_json['data']['ean'],
        'productName': response_json['data']['products'][0]['name'],
        'stores': stores,
        'image': response_json['data']['products'][0]['image'],
        'description': description
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
    x = 1
    for code in ean.values():
        if x % 60 == 0:
            print('sleeping')
            time.sleep(60)
            print('waking up')
        x += 1
        product = get_product(code)
        print(product)
        if product is None:
            continue
        update_product(product).get('status')
    return {'status': 200}

update_db()