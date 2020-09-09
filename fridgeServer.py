from fridge.fridge import FridgeThread, SlabFridge
from app import app

from flask import jsonify
from flask import request
from flask import make_response

fridge = None

@app.route("/get/temps")
def get_temps():
    return jsonify(fridge.get_temperatures())

@app.route("/get/state")
def get_state():
    return jsonify(state=fridge.get_automation_state(),subroutine=fridge.get_subroutine_state())

@app.route("/get/switches")
def get_switches():
    return jsonify(fridge.get_heatswitch_states())

@app.route("/set/switch",methods=['POST'])
def set_switch():
    #{'name':'1k_hs','value':'False'}
    sw_name = request.form.get('name')
    value = request.form.get('value')=='true'
    fridge.set_heatswitch(sw_name,value)
    print('Setting',sw_name,' to: ',value)
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
        
if __name__ == "__main__":
    print('Starting automation thread')
    fridge = SlabFridge(configfile="fridge/Breton.json",useInflux=True,logStateOnly=True)
    automation_thread = FridgeThread(fridge,False)
    automation_thread.start()
    fridge.automation_thread = automation_thread
    
    print('Starting app.')
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
    #app.debug=True
    #app.run(host="0.0.0.0")
    
    #on app closed
    automation_thread.exit = True
    



