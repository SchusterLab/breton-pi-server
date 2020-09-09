from flask import Flask#, url_for
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix

app = Flask(__name__)
app.config['REVERSE_PROXY_PATH'] = '/flask'
ReverseProxyPrefixFix(app)

from app import views
