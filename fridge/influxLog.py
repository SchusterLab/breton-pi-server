"""
Created on Fri May 22 14:18:11 2020

@author: sasha
"""
import time
import logging

client = None

def setupDatabase(host = 'localhost',port = 8086,USER = 'slab',PASSWORD = 'slab',DBNAME = 'breton'):
    from influxdb import InfluxDBClient
    from influxdb.client import InfluxDBClientError
    from influxdb.client import InfluxDBServerError
    
    # Setup InfluxdB Client
    try:
        client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)
    except InfluxDBClientError:
        logging.error('Error: cannot connect to InfluxDb!')
        return None

    logging.info("Connecting to database: " + DBNAME)

    # Alter retention policies
    #rp_default = 'server_data'
    #rp_fdata = 'fridge_data'
    
    return client

def logToInflux(TempDict,client=None,State=None,Pressure=None):
    #send data to influx
    json_body = [{
            "measurement":"temp_K",
            "tags":{
                "thermometer":key
            },
            "fields":{
                "value":float(tmp)
            }
        } for key,tmp in TempDict.items()]
    if State is not None:
        json_body.append({
            "measurement":"state",
            "fields":{
                "value":State
            }})
    if Pressure is not None:
        #assume pressure is in the form of a list of dictionaries
        #values and gauges are hard baked for now
        #TODO make the pressure section general
        json_body.append({
            "measurement":"pressure",
            "tags":{
                "gauge":"P_he",
                "units":Pressure[0]["units"]
                },
            "fields":{
                "value":float(Pressure[0]["pressure"]),
                "voltage":float(Pressure[0]["voltage"])
            }})
        json_body.append({
                    "measurement":"pressure",
                    "tags":{
                        "gauge":"P_ovc",
                        "units":Pressure[1]["units"]
                        },
                    "fields":{
                        "value":float(Pressure[1]["pressure"]),
                        "voltage":float(Pressure[1]["voltage"])
                    }})
    if client is None:
        setupDatabase()
    else:
        try:
            client.write_points(json_body,retention_policy='fridge_data')
        except Exception:
            #print(e)
            logging.error('Error Writing points!')
