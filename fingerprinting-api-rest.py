from flask import Flask, request
from pymongo import MongoClient
import json

app = Flask(__name__)


@app.route('/fingerprint', methods=['POST'])
def add_fingerprint():
    return insert_fingerprint(request.json)


def insert_fingerprint(fingerprint):
    client = MongoClient()
    db = client.rcmmDB
    insert_result = db.fingerprint.insert_one(fingerprint)
    result_dict = dict()
    result_dict['fingerprint_id'] = str(insert_result.inserted_id)
    return json.dumps(result_dict)


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=6969)
