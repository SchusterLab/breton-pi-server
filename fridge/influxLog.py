"""
Created on Fri May 22 14:18:11 2020

@author: sasha
"""
import time

client = None

def setupDatabase(host = 'localhost',port = 8086,USER = 'slab',PASSWORD = 'slab',DBNAME = 'breton'):
    from influxdb import InfluxDBClient
    from influxdb.client import InfluxDBClientError
    from influxdb.client import InfluxDBServerError
    
    # Setup InfluxdB Client
    try:
        client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)
    except InfluxDBClientError:
        print('Error: cannot connect to InfluxDb!')

    print("Connecting to database: " + DBNAME)

    # Alter retention policies
    rp_default = 'server_data'
    rp_fdata = 'fridge_data'
    
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
        json_body.append({
            "measurement":"pressure",
            "tags":{
                "gauge":"P_he"
                },
            "fields":{
                "value":float(Pressure)
            }})
    if client is None:
        setupDatabase()
    else:
        try:
            result = client.write_points(json_body,retention_policy='fridge_data')
        except Exception as e:
            print(e)
            print(time.strftime("%D-%H:%M:%S"),'Error Writing points!')
