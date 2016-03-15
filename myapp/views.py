from myapp import app
from models_realtime import RealtimeDelayPrediction
from models_database import GTFS, Weather, Traffic, stdout

@app.route('/')
@app.route('/index')
def index():
	return 'Hello'


@app.route('/test')
def test():
	global stdout
	return str(stdout)