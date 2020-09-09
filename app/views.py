from flask import jsonify
from flask import render_template
from flask import request
from flask_cors import CORS, cross_origin

from app import app


@app.route("/")
@app.route("/control")
def control():
    #print(request.headers)
    return render_template("control.html",title='Control')

@app.route("/status")
def status():
    #print(request.headers)
    return render_template("status.html",title='Status')

@app.route("/settings")
def settings():
    #print(request.headers)
    return render_template("settings.html",title='Status')

@app.route("/panel/control")
@cross_origin()
def panel_control():
    return render_template("panel_control.html")

@app.route("/panel/status")
@cross_origin()
def panel_status():
    return render_template("panel_status.html")
      
@app.route('/ping')
@cross_origin()
def ping():
    return "pong"
