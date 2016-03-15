import pymongo
from pymongo import MongoClient
from math import radians, cos, sin, asin, sqrt

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

# connection = MongoClient(MONGODB_HOST, MONGODB_PORT)

class RealtimeDelayPrediction:

	def __init__(self):
		pass

	# calculate distance (km) between two coordinates
	def calculateDistance(self, lon1, lat1, lon2, lat2):
		lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
		# haversine formula 
		dlon = lon2 - lon1 
		dlat = lat2 - lat1 
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
		c = 2 * asin(sqrt(a)) 
		km = 6367 * c
		return km

	def test(self):
		connection = MongoClient("129.59.107.160", 27017)
		print connection["thub_database"].collection_names()
		col = connection["thub_database"]['alerts']
		tpResults = col.find()
		count=0
		for tpResult in tpResults:
			count+=1
			if count>10:
				break
			print tpResult

	