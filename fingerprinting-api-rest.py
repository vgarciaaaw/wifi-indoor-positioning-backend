from flask import Flask, request, send_from_directory
from pymongo import MongoClient
import json
import pandas as pd
import os

app = Flask(__name__)


@app.route('/fingerprint', methods=['POST'])
def add_fingerprint():
    return insert_fingerprint(request.json)


@app.route('/location', methods=['POST'])
def add_location():
    return insert_location(request.json)


@app.route('/fingerprint/csv')
def get_fingerprint_csv():
    df = pd.DataFrame(list(get_fingerprint_collection().find()))
    df.to_csv(path_or_buf=os.path.dirname(os.path.abspath(__file__)) + '/fingerprint.csv', encoding='utf-8',
              index=False)
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename='fingerprint.csv', as_attachment=True)


def get_database():
    client = MongoClient()
    return client.rcmmDB


def get_fingerprint_collection():
    return get_database().fingerprint


def get_location_collection():
    return get_database().location


def insert_fingerprint(fingerprint):
    insert_result = get_fingerprint_collection().insert_one(fingerprint)
    result_dict = dict()
    result_dict['fingerprint_id'] = str(insert_result.inserted_id)
    return json.dumps(result_dict)


def insert_location(location):
    insert_result = get_location_collection().insert_one(location)
    result_dict = dict()
    result_dict['location_id'] = str(insert_result.inserted_id)
    return json.dumps(result_dict)


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=6969)
