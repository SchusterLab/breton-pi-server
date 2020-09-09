"""
Created on Fri May 22 14:18:11 2020

@author: sasha
"""
import time

client = None

def setupDatabase(host = 'localhost',port = 8086,USER = 'root',PASSWORD = 'root',DBNAME = 'breton_test'):
    from influxdb import InfluxDBClient
    from influxdb.client import InfluxDBClientError
    from influxdb.client import InfluxDBServerError
    
    # Setup InfluxdB Client
    try:
        client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)
    except InfluxDBClientError:
        print('Error: cannot connect to InfluxDb!')

    print("Connecting to database: " + DBNAME)
    
    print(client.get_list_retention_policies(DBNAME))
    # Alter retention policies
    rp_default = 'server_data'
    #client.create_retention_policy(rp_default, '1d', 2, default=True)
    rp_fdata = 'fridge_data'
    #client.create_retention_policy(rp_fdata, '8w', 2, shard_duration='1d',default=False)
    #client.create_retention_policy(rp_fdata, '3d', 2, default=False)
    
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
            "measurement":"pressure_He",
            "tags":{
                "location":"P1"
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
