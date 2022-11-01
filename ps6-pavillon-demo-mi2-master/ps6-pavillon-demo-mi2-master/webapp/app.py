"""
Copyright (c) 2021 University of Applied Sciences Western Switzerland / Fribourg

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

 Project: HEIA-FR / Measure meteorological data for the DEMO_MI2 modular pavillon 

 Purpose: This module is the main module for the application. It measure, saves and 
 send the data from devices connected to itself.

 Author:  Denis Rosset et Julien Piguet
 Date:    Mai 2021
"""
from flask import Flask
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import requests
import json
import dateutil.parser
from flask import Flask, render_template, request
import Configuration

most_recent_measure = datetime.now()
app = Flask(__name__)

TIME_DELTA_FOR_LIVE_MIN = 15 # Delta time for live status

# Application root Route
# Return: index html page
@app.route('/')
def root(name=None):
    connect()
    is_live()
    return render_template('index.html', name=name)


# Is live status route
# Return: Application status
@app.route('/is-live')
def is_live():
    result = {"islive":False}
    # Set time range from one year ago to now
    start_of_day = datetime.combine(datetime.today(), time.min)
    end_of_day = start_of_day + timedelta(days=1)
    start_of_year_iso = (start_of_day - timedelta(days=365)).isoformat()
    end_of_day_iso = end_of_day.isoformat()
    # Get stats from the last year for each sensor
    datas = []
    sensor_list = ["temp", "humi", "suni", "glob", "wind"]
    for name in sensor_list:
        data = get_data(start_of_year_iso, end_of_day_iso, name, interior=True, stats=True)
        ts = dateutil.parser.parse(data["lastTs"], ignoretz=False)
        datas.append(ts.timestamp())
    global most_recent_measure
    # Get the most recent data
    most_recent_measure = datetime.fromtimestamp(max(datas))
    result["date_last_measure"] = datetime.fromtimestamp(max(datas)).strftime("%d %b %Y")
    # Most recent data must be in the last Delta minutes to be online
    if(max(datas) > (datetime.today() - timedelta(minutes=TIME_DELTA_FOR_LIVE_MIN)).timestamp()):
         result["islive"] = True
    result["location"] = Configuration.LOCATION
    # Return response as JSON
    return json.dumps(result)


# Get data route
# Input: type name (string)
# Return: All data for type and most recent measure day
@app.route('/get-data')
def get_measures_from_last_day_available(type=None):
    result = {}
    result = {"data": [], "date": "", "type": ""}
    if type is None:
        type = request.args.get('type')
    result["type"] = type

    global most_recent_measure
    start_of_last_day_of_measure = datetime.combine(most_recent_measure, time.min)
    end_of_last_day_of_measure = start_of_last_day_of_measure + timedelta(days=1)

    # Sun and polution have only one value
    if type == "suni" or type == "polu":
        df_last_day = get_data(start_of_last_day_of_measure.isoformat(), end_of_last_day_of_measure.isoformat(), type, False) # Get data
        # If no data, return an empty csv
        if df_last_day.empty: 
            df_last_day = pd.DataFrame(columns=['timestamp', 'value'])
            result["lastint"] = "Offline"
        else:
            # Dropping lines with test
            df_last_day = df_last_day[df_last_day.comment != "test"]
            df_last_day = df_last_day.drop(['objectId', 'comment'], axis=1)
            df_last_day['timestamp'] = df_last_day['timestamp'].apply(lambda dt: dateutil.parser.parse(dt, ignoretz=False))
            # Round suni values
            if type == "suni":
                df_last_day['value'] = df_last_day['value'].astype(float)
                df_last_day['value'] = df_last_day['value'].astype(int)
                df_last_day['value'] = df_last_day['value'].astype(str)
            # last is Offline if there is no data since delta time
            if (df_last_day.loc[df_last_day.index[-1], "timestamp"].timestamp() < (datetime.today() - timedelta(minutes=TIME_DELTA_FOR_LIVE_MIN)).timestamp()):
                result["last"] = "Offline"
            else:
                result["last"] = df_last_day.loc[df_last_day.index[-1], "value"]
            # Rename columns and format time
            df_last_day = df_last_day.rename(columns={"timestamp": "timestamp", "value": "Extérieur"})
            df_last_day['timestamp'] = df_last_day['timestamp'].apply(lambda dt: dt.isoformat())


    else:
        df_interior_last_day = get_data(start_of_last_day_of_measure.isoformat(), end_of_last_day_of_measure.isoformat(), type, True) # Get data
        # If no data, return an empty csv
        if df_interior_last_day.empty:
            df_interior_last_day = pd.DataFrame(columns=['timestamp', 'value'])
            result["lastint"] = "Offline"
        else:
            # Dropping lines with test
            df_interior_last_day = df_interior_last_day[df_interior_last_day.comment != "test"]
            df_interior_last_day = df_interior_last_day.drop(['objectId', 'comment'], axis=1)
            # Round timestamp to minute
            df_interior_last_day['timestamp'] = df_interior_last_day['timestamp'].apply(lambda dt: dateutil.parser.parse(dt, ignoretz=False))
            df_interior_last_day['timestamp'] = df_interior_last_day['timestamp'].dt.round('min')

            # lastint is Offline if there is no data since delta time
            if (df_interior_last_day.loc[df_interior_last_day.index[-1], "timestamp"].timestamp() < (datetime.today() - timedelta(minutes=TIME_DELTA_FOR_LIVE_MIN)).timestamp()):
                result["lastint"] = "Offline"
            else:
                result["lastint"] = df_interior_last_day.loc[df_interior_last_day.index[-1], "value"]


        df_exterior_last_day = get_data(start_of_last_day_of_measure.isoformat(), end_of_last_day_of_measure.isoformat(), type, False) # Get data

        if df_exterior_last_day.empty:
            df_exterior_last_day = pd.DataFrame(columns=['timestamp', 'value'])
            result["lastext"] = "Offline"
        else:
            # Dropping lines with test
            df_exterior_last_day = df_exterior_last_day[df_exterior_last_day.comment != "test"]
            df_exterior_last_day = df_exterior_last_day.drop(['objectId', 'comment'], axis=1)
            # Round timestamp to minute
            df_exterior_last_day['timestamp'] = df_exterior_last_day['timestamp'].apply(lambda dt: dateutil.parser.parse(dt, ignoretz=False))
            df_exterior_last_day['timestamp'] = df_exterior_last_day['timestamp'].dt.round('min')

            # lastext is Offline if there is no data since delta time
            if (df_exterior_last_day.loc[df_exterior_last_day.index[-1], "timestamp"].timestamp() < (datetime.today() - timedelta(minutes=TIME_DELTA_FOR_LIVE_MIN)).timestamp()):
                result["lastext"] = "Offline"
            else:
                result["lastext"] = df_exterior_last_day.loc[df_exterior_last_day.index[-1], "value"]

        # Merge int and ext values by timestamp (outer merge)
        df_last_day = pd.merge(df_interior_last_day, df_exterior_last_day, how='outer', on='timestamp', suffixes=('_int', '_ext'))
        df_last_day = df_last_day.sort_values(by=['timestamp'])
        # Rename columns and format time
        df_last_day = df_last_day.rename(columns={"timestamp": "timestamp", "value_int": "Intérieur", "value_ext": "Extérieur"})
        df_last_day['timestamp'] = df_last_day['timestamp'].apply(lambda dt: dt.isoformat())

    # Save data in the response
    result["data"] = df_last_day.to_csv(index=False)
    result["date"] = most_recent_measure.strftime("%d/%m/%Y")
    # Return response as JSON
    return json.dumps(result)

# Get data from BBData
# Input: start (date), end (date), type (string), interior (boolean), stats (boolean),
# Return: Data for type in a range of time (start to end)
def get_data(start, end, type, interior=True, stats=False):
    if type == "humi":
        OBJECT_ID_INTERIOR = 13560
        OBJECT_ID_EXTERIOR = 13565
    elif type == "suni":
        OBJECT_ID_INTERIOR = 13561
        OBJECT_ID_EXTERIOR = 13566
    elif type == "temp":
        OBJECT_ID_INTERIOR = 13562
        OBJECT_ID_EXTERIOR = 13567
    elif type == "glob":
        OBJECT_ID_INTERIOR = 13563
        OBJECT_ID_EXTERIOR = 13568
    elif type == "wind":
        OBJECT_ID_INTERIOR = 13564
        OBJECT_ID_EXTERIOR = 13569
    elif type == "polu":
        OBJECT_ID_INTERIOR = 13545
        OBJECT_ID_EXTERIOR = 13545
    if(stats):
        if interior:
            ENDPOINT = "https://bbdata-admin.smartlivinglab.ch/api/objects/{}/stats".format(OBJECT_ID_INTERIOR)
        else:
            ENDPOINT = "https://bbdata-admin.smartlivinglab.ch/api/objects/{}/stats".format(OBJECT_ID_EXTERIOR)
    else:
        if interior:
            ENDPOINT = "https://bbdata-admin.smartlivinglab.ch/api/objects/{}/values?from={}&to={}".format(OBJECT_ID_INTERIOR, start,end)
        else:
            ENDPOINT = "https://bbdata-admin.smartlivinglab.ch/api/objects/{}/values?from={}&to={}".format(OBJECT_ID_EXTERIOR, start,end)

    response = requests.get(ENDPOINT, headers=getHeaders())
    response.json()
    if(stats):
        return response.json()
    else:
        return pd.DataFrame(response.json())

# Establish connection with BBData
# Return: Headers with authentication tokens
def connect():
    ENDPOINT="https://bbdata-admin.smartlivinglab.ch/api/login"
    USERNAME="denis.rosset"
    PASSWORD="MzYf5gfM5tyceFcz"
    creds={"username": USERNAME, "password": PASSWORD}
    response=requests.post(ENDPOINT, json=creds)
    response.json()

    USER_ID=str(response.json()["userId"])
    API_KEY=str(response.json()["secret"])

    headers={
        'bbuser': USER_ID,
        'bbtoken':  API_KEY
    }
    setHeaders(headers)

    return headers

global_headers = {}

# Store headers
def setHeaders(headers):
    global global_headers
    global_headers = headers

# Return a copy of global stored headers
def getHeaders():
    global global_headers
    temp = global_headers
    return temp

if __name__ == "__main__":
    app.run(host='localhost')