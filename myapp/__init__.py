from flask import Flask
app = Flask(__name__)

#import ssl
#sSLContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
#sSLContext.load_cert_chain(certfile="myapp/cert.pem", keyfile="myapp/cert.pem")

#APScheduler
from flask_apscheduler import APScheduler
from myapp.jobs import Config
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)

from myapp import views
from myapp import models_database