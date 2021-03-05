from fridge.fridge import FridgeThread, SlabFridge
from app import app

from flask import jsonify
from flask import request
from flask import make_response
from flask import send_file
from flask import abort

import os

#   --- Setup logging config ---

import logging
import logging.config

try:
    logging.config.fileConfig('logging.conf')
except:
    print('Unable to create logfile!')

#   --- Setup flask routing ---

fridge = None

@app.route("/get/temps")
def get_temps():
    return jsonify(fridge.get_temperatures())

@app.route("/get/pressure")
def get_pressure():
    #TODO implement url aruments to select which pressure gauge
    return jsonify(fridge.get_pressure_data())

@app.route("/get/state")
def get_state():
    return jsonify(state=fridge.get_automation_state(),subroutine=fridge.get_subroutine_state())

@app.route("/get/switches")
def get_switches():
    return jsonify(fridge.get_heatswitch_states())

@app.route("/get/status/compressor")
def get_status_compressor():
    return jsonify(fridge.get_compressor_status())

@app.route("/get/status/bk")
def get_status_bk():
    #TODO: make this a threaded call, or cache a local copy and update
    return jsonify(voltages=fridge.ps.measure_voltages())

@app.route("/get/logs")
def log_listing():
    BASE_DIR = '/var/log/fridge'
    path = os.path.join(BASE_DIR,'fridge.log')

    if not os.path.exists(path):
        return abort(404)

    if os.path.isfile(path):
        return send_file(path)
    else:
        return os.listdir(path)
@app.route("/set/compressor",methods=['POST'])
def set_compressor():
    value = request.form.get('value')=='true'
    #TODO authentication here
    logging.info('%s setting compressor to: %s',request.host_url,value)
    fridge.set_compressor_status(value)
    return 'set'

@app.route("/set/switch",methods=['POST'])
def set_switch():
    #{'name':'1k_hs','value':'False'}
    sw_name = request.form.get('name')
    value = request.form.get('value')=='true'
    fridge.set_heatswitch(sw_name,value)
    logging.info('%s setting %s to: %s',request.host_url,sw_name,value)
    return 'set'

@app.route("/set/automation/subroutine",methods=['POST'])
def set_subroutine():
    subroutine = request.form.get('subroutine')
    fridge.set_subroutine_state(subroutine)
    return 'set'

@app.route("/set/automation/state",methods=['POST'])
def set_state():
    state = request.form.get('state')
    if state == 'STOP':
        fridge.stop_automation()
    else:
        fridge.set_automation_state(state)
    return 'set'

#   --- main ---
        
if __name__ == "__main__":
    logging.info('Starting automation thread')
    fridge = SlabFridge(configfile="fridge/Breton.json",useInflux=True)
    automation_thread = FridgeThread(fridge)
    automation_thread.start()
    fridge.automation_thread = automation_thread
    
    logging.info('Starting app.')
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
    #app.debug=True
    #app.run(host="0.0.0.0")
    
    #on app closed
    automation_thread.exit = True
    



