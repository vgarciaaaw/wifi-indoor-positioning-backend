from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient
import json
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
socketio = SocketIO(app)


# Web Frontend
@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html', data=json.dumps(get_locations()))


@app.route('/livelocation')
def livelocation():
    return render_template('livelocation.html')


# API methods
@app.route('/fingerprint', methods=['POST'])
def add_fingerprint():
    return insert_fingerprint(request.json['fingerprinting'])


@app.route('/location', methods=['POST'])
def add_location():
    return insert_location(request.json)


@app.route('/fingerprint/csv')
def get_fingerprint_csv():
    df = pd.DataFrame(list(get_fingerprint_collection().find()))
    df.to_csv(path_or_buf=os.path.dirname(os.path.abspath(__file__)) + '/fingerprint.csv', encoding='utf-8',
              index=False)
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename='fingerprint.csv',
                               as_attachment=True)


@app.route('/attributes/config')
def get_attributes_config():
    df = pd.DataFrame(list(get_fingerprint_collection().find()))
    attributes = df.columns.values
    index = 0
    to_delete_indexes = []
    for attribute in attributes:
        if attribute == '_id' or attribute == 'lat' or attribute == 'lng' or attribute == 'waypoint_id':
            to_delete_indexes.append(index)
        index += 1
    attributes = np.delete(attributes, to_delete_indexes)
    attributes_json = create_dictionary_for_attributes(attributes)
    with open(os.path.dirname(os.path.abspath(__file__)) + '/attributes.config', 'w', encoding='utf-8') as file:
        file.write(json.dumps(attributes_json))
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename='attributes.config',
                               as_attachment=True)


@app.route('/classes/config')
def get_classes_config():
    waypoint_cursor = get_waypoint_collection().find()
    waypoint_list = list()
    for waypoint in waypoint_cursor:
        waypoint_dict = dict()
        waypoint_dict['class_id'] = str(waypoint['_id'])
        waypoint_dict['lat'] = waypoint['lat']
        waypoint_dict['lng'] = waypoint['lng']
        waypoint_list.append(waypoint_dict)
    with open(os.path.dirname(os.path.abspath(__file__)) + '/classes.config', 'w', encoding='utf-8') as file:
        file.write(json.dumps(waypoint_list))
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename='classes.config',
                               as_attachment=True)


# SocketIO
@socketio.on('location')
def location_received(location):
    socketio.emit('location', location)


# CRUD and mapping methods
def parse_fingerprint(fingerprinting):
    fingerprint_dict = dict()
    waypoint = dict()
    for fingerprint in fingerprinting:
        fingerprint_dict[fingerprint['mac']] = fingerprint['rssi']
    fingerprint_dict['lat'] = fingerprinting[0]['lat']
    waypoint['lat'] = fingerprinting[0]['lat']
    fingerprint_dict['lng'] = fingerprinting[0]['lon']
    waypoint['lng'] = fingerprinting[0]['lon']
    fingerprint_dict['waypoint_id'] = find_waypoint_id(waypoint)
    return fingerprint_dict


def get_database():
    client = MongoClient()
    return client.rcmmDB


def get_fingerprint_collection():
    return get_database().fingerprint


def get_location_collection():
    return get_database().location


def get_waypoint_collection():
    return get_database().waypoint


def insert_fingerprint(fingerprint):
    insert_result = get_fingerprint_collection().insert_one(parse_fingerprint(fingerprint))
    result_dict = dict()
    result_dict['fingerprinting_id'] = str(insert_result.inserted_id)
    return json.dumps(result_dict)


def insert_location(location):
    insert_result = get_location_collection().insert_one(location)
    result_dict = dict()
    result_dict['location_id'] = str(insert_result.inserted_id)
    return json.dumps(result_dict)


def insert_waypoint(waypoint):
    insert_result = get_waypoint_collection().insert_one(waypoint)
    return insert_result.inserted_id


def find_waypoint_id(waypoint):
    find_result = get_waypoint_collection().find_one(waypoint)
    if find_result == None:
        find_result = insert_waypoint(waypoint)
    else:
        find_result = find_result['_id']
    return find_result


def create_dictionary_for_attributes(attributes_ndarray):
    attributes_list = list()
    for attribute in attributes_ndarray:
        attribute_dict = dict()
        attribute_dict['attribute_name'] = attribute
        attributes_list.append(attribute_dict)
    return attributes_list


def get_locations():
    location_list = list()
    locations = get_location_collection().find()
    for location in locations:
        location_dict = dict()
        location_dict['lat'] = location['lat']
        location_dict['lng'] = location['lng']
        location_list.append(location_dict)
    return location_list


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=6969)
