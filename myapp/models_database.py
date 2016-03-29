import pymongo
from pymongo import MongoClient
# from math import radians, cos, sin, asin, sqrt
import requests
import zipfile
from io import BytesIO
import StringIO, pickle, csv
import thread
import time
from sets import Set
import pycurl
import cStringIO
import json
import datetime
from myapp import scheduler
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
import urllib, sys
from bson.objectid import ObjectId

MONGODB_HOST = 'localhost'
# MONGODB_HOST = '129.59.107.160'
MONGODB_PORT = 27017
connection = MongoClient(MONGODB_HOST, MONGODB_PORT)

global cached_map_linkID_details
cached_map_linkID_details = {}

global stdout
stdout = []

def request_realtime_weather_data():
	weather = Weather()
	weather.requestWeatherForAllCounty()

def request_realtime_traffic_data():
	traffic = Traffic()
	traffic.requestTrafficForAllRoutes()

def request_static_gtfs_data():
	gTFS = GTFS()
	gTFS.requestAllVersions()

def request_realtime_gtfs_data():
	gTFS = GTFS()
	gTFS.requestRealtimeGTFSData()

class Traffic:

	HERE_APP_ID = 'oxFV8daRXZafXLI87l7o'
	HERE_APP_CODE = '1Af5pCupGbm6NrfnWxPDsg'
	DB_NAME = 'thub_traffic'
	COLLECTION_NAME = 'realtime_data'
	# DB_NAME = 'augmenteddb'
	# COLLECTION_NAME = 'traffic'
	COLLECTION_SHAPEID_LINKID_NAME = 'shapeid_linkid'
	COLLECTION_LINKID_DETAILS_NAME = 'linkid_details'
	COLLECTION_SHAPEID_COORS_NAME = 'shapeid_coordinates'
	


	def __init__(self):
		pass

	def getMapShapes(self):
		global stdout
		stdout.append("getMapShapes")
		# Check if exist in db
		db_collection = connection[self.DB_NAME][self.COLLECTION_SHAPEID_COORS_NAME]
		gTFS = GTFS()
		gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		tpResults = db_collection.find({'dbName': gtfs_db_name})
		for tpResult in tpResults:
			return tpResult['data']


		set_shapeID = Set([])

		# get current static gtfs trips
		gTFS = GTFS()
		gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		tpResults = connection[gtfs_db_name]['trips'].find()
		for tpResult in tpResults:
			set_shapeID.add(tpResult['shape_id'])

		map_shape = {}
		for shapeID in set_shapeID:
			stdout.append(str(len(map_shape.keys()))+'/'+str(len(set_shapeID)))
			print str(len(map_shape.keys()))+'/'+str(len(set_shapeID))
			array_coordinates = []
			tpResults = connection[gtfs_db_name]['shapes'].find({'shape_id':shapeID}) \
				.sort([['shape_pt_sequence', pymongo.ASCENDING]])
			for tpResult in tpResults:
				array_coordinates.append([tpResult['shape_pt_lat'], tpResult['shape_pt_lon']])
			map_shape[shapeID] = array_coordinates

		db_collection = connection[self.DB_NAME][self.COLLECTION_SHAPEID_COORS_NAME]
		db_collection.remove({'dbName': gtfs_db_name})
		db_collection.insert({'dbName': gtfs_db_name, 'data':map_shape})
		return map_shape

	def sendRequestsToCalculateRoute(self):
		global stdout
		stdout.append("sendRequestsToCalculateRoute")
		if self.checkCachedMapShouldBeUpdated():
			pass
		else:
			db_collection = connection[self.DB_NAME][self.COLLECTION_LINKID_DETAILS_NAME]
			gTFS = GTFS()
			gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
			tpResults = db_collection.find({'dbName': gtfs_db_name})
			for tpResult in tpResults:
				return tpResult['data']
		map_shape = self.getMapShapes()
		map_linkID_details = {}
		map_shapeID_linkID = {}

		index=0
		map_shapeID_coordinates = {}
		iii=0
		stdout.append("start calculate routes")
		for shapeID in map_shape.keys():
			map_shapeID_coordinates[shapeID] = []
			routing_req = "http://route.cit.api.here.com/routing/7.2/calculateroute.json?app_id="+self.HERE_APP_ID+"&app_code="+self.HERE_APP_CODE
			routing_req += "&mode=fastest;publicTransport"
			# print len(map_shape[shapeID][::3])
			# continue
			step = 100
			# array_coordinates = map_shape[shapeID][::3]
			array_coordinates = map_shape[shapeID]
			for i in range(0, len(array_coordinates)):
				if i%step == 0:
					if i!=0:
						map_shapeID_coordinates[shapeID][-1].append(array_coordinates[i])
					if i!= len(array_coordinates)-1:		# make sure there are at least two waypoints in each array
						map_shapeID_coordinates[shapeID].append([])
				map_shapeID_coordinates[shapeID][-1].append(array_coordinates[i])
			array_url = []
			for i in range(0, len(map_shapeID_coordinates[shapeID])):
				url_request = routing_req
				for j in range(0, len(map_shapeID_coordinates[shapeID][i])):
					url_request += "&waypoint" + str(j) + "=geo!" + str(map_shapeID_coordinates[shapeID][i][j][0])+","+str(map_shapeID_coordinates[shapeID][i][j][1])
				array_url.append(url_request)

			m = pycurl.CurlMulti()
			reqs = []
			for one_url in array_url:
				response = cStringIO.StringIO()
				handle = pycurl.Curl()
				handle.setopt(pycurl.URL, one_url)
				handle.setopt(pycurl.WRITEFUNCTION, response.write)
				req = (one_url, response, handle)
				m.add_handle(req[2])
				reqs.append(req)
			SELECT_TIMEOUT = 1.0
			num_handles = len(reqs)
			while num_handles:
				ret = m.select(SELECT_TIMEOUT)
				if ret==-1: continue
				while 1:
					ret, num_handles = m.perform()
					if ret != pycurl.E_CALL_MULTI_PERFORM: 
						break
			map_shapeID_linkID[shapeID] = []
			for req in reqs:
				# print req[1].getvalue()
				response_string = req[1].getvalue()
				# print 'response_string', response_string
				response_json = json.loads(response_string)
				response = response_json.get("response")
				if response is None:
					continue
				route = response.get("route")
				if route is None:
					continue
				waypoints = route[0].get("waypoint")
				for waypoint in waypoints:
					linkid = waypoint.get("linkId")
					if linkid.startswith("+"):
								linkid = linkid[1:]
					mappedPosition = waypoint.get("mappedPosition")
					originalPosition = waypoint.get("originalPosition")
					shapeIndex =  waypoint.get("shapeIndex")
					entry_map_linkID = map_linkID_details.get(linkid)
					if entry_map_linkID == None:
						entry_map_linkID = {}
						entry_map_linkID["mappedPosition"] = mappedPosition
						entry_map_linkID["originalPosition"] = originalPosition
						entry_map_linkID["shapeIndex"] = [shapeIndex]
						map_linkID_details[linkid] = entry_map_linkID
					# else:
					# 	if entry_map_linkID["mappedPosition"] != mappedPosition:
					# 		print 'waypoint', waypoint
					# 		print 'entry_map_linkID', entry_map_linkID
					map_shapeID_linkID[shapeID].append(linkid)
					# print '%f,%f' % (mappedPosition['latitude'], mappedPosition['longitude'])
			
			# print 'map_shapeID_linkID: ', map_shapeID_linkID
			# print 'map_linkID_details', map_linkID_details
			iii+=1
			sssss = ' $ progress:'+str(iii)+'/'+str(len(map_shape.keys()))
			stdout.append(sssss)
			print sssss
			# if iii>5:
			# 	break
			# for request_url in array_url:
			# 	stdout.append(request_url)
			# 	buf = cStringIO.StringIO()
			# 	c = pycurl.Curl()
			# 	c.setopt(c.URL, request_url)
			# 	c.setopt(c.WRITEFUNCTION, buf.write)
			# 	stdout.append("request_url beforeperform")
			# 	c.perform()
			# 	stdout.append("request_url perform")
			# 	response_string = buf.getvalue()
			# 	# print 'response_string', response_string
			# 	response_json = json.loads(response_string)
			# 	response = response_json.get("response")
			# 	stdout.append("request_url response")
			# 	if response is None:
			# 		continue
			# 	route = response.get("route")
			# 	if route is None:
			# 		continue
			# 	waypoints = route[0].get("waypoint")
			# 	stdout.append("request_url waypoints"+str(len(waypoints)))
			# 	for waypoint in waypoints:
			# 		linkid = waypoint.get("linkId")
			# 		if linkid.startswith("+"):
			# 					linkid = linkid[1:]
			# 		mappedPosition = waypoint.get("mappedPosition")
			# 		originalPosition = waypoint.get("originalPosition")
			# 		shapeIndex =  waypoint.get("shapeIndex")
			# 		entry_map_linkID = map_linkID_details.get(linkid)
			# 		if entry_map_linkID == None:
			# 			entry_map_linkID = {}
			# 			entry_map_linkID["mappedPosition"] = mappedPosition
			# 			entry_map_linkID["originalPosition"] = originalPosition
			# 			entry_map_linkID["shapeIndex"] = [shapeIndex]
			# 			map_linkID_details[linkid] = entry_map_linkID
			# 		# else:
			# 		# 	if entry_map_linkID["mappedPosition"] != mappedPosition:
			# 		# 		print 'waypoint', waypoint
			# 		# 		print 'entry_map_linkID', entry_map_linkID
			# 		map_shapeID_linkID[shapeID].append(linkid)

			# iii+=1
			# sssss = ' $ progress:'+str(iii)+'/'+str(len(map_shape.keys()))
			# stdout.append(sssss)
			# print sssss
			# # if iii>3:
			# # 	break

		# save_obj(map_linkID_details, "map_linkID_details")
		# save_obj(map_shapeID_linkID, "map_shapeID_linkID")
		db_collection = connection[self.DB_NAME][self.COLLECTION_LINKID_DETAILS_NAME]
		gTFS = GTFS()
		gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		db_collection.remove({'dbName': gtfs_db_name})
		db_collection.insert({'dbName': gtfs_db_name, 'data':map_linkID_details})

		db_collection = connection[self.DB_NAME][self.COLLECTION_SHAPEID_LINKID_NAME]
		gTFS = GTFS()
		gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		db_collection.remove({'dbName': gtfs_db_name})
		db_collection.insert({'dbName': gtfs_db_name, 'data':map_shapeID_linkID})

		return map_linkID_details

	def checkCachedMapShouldBeUpdated(self):
		global stdout
		stdout.append("checkCachedMapShouldBeUpdated")
		flag_shapeID_linkID = False
		db_collection = connection[self.DB_NAME][self.COLLECTION_SHAPEID_LINKID_NAME]
		gTFS = GTFS()
		gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		tpResults = db_collection.find({'dbName': gtfs_db_name})
		for tpResult in tpResults:
			flag_shapeID_linkID = True
			break
		flag_linkID_details = False
		db_collection = connection[self.DB_NAME][self.COLLECTION_LINKID_DETAILS_NAME]
		tpResults = db_collection.find({'dbName': gtfs_db_name})
		for tpResult in tpResults:
			flag_linkID_details = True
			break
		if flag_linkID_details and flag_shapeID_linkID:
			return False
		else:
			return True



	def downloadTrafficForAllLinks(self):
		global stdout
		stdout.append("downloadTrafficForAllLinks")
		global cached_map_linkID_details
		map_linkID_traffic = {}
		link_req = "https://route.st.nlp.nokia.com/routing/6.2/getlinkinfo.json?app_id="+self.HERE_APP_ID+"&app_code="+self.HERE_APP_CODE
		link_req += "&metricSystem=imperial&linkAttributes=speedLimit,dynamicSpeedInfo&linkIds="
		step=600
		array_url=[]
		url_request = None
		array_linkID = cached_map_linkID_details.keys()
		for i in range(0, len(array_linkID)):
			if i%step==0:
				if i!=0:
					array_url.append(url_request)
				url_request = link_req
				url_request += array_linkID[i]
			else:
				url_request += ','+array_linkID[i]
		if (len(array_linkID)%step)!=0:
			array_url.append(url_request)

		# for request_url in array_url:
		# 	buf = cStringIO.StringIO()
		# 	c = pycurl.Curl()
		# 	c.setopt(c.URL, request_url)
		# 	c.setopt(c.WRITEFUNCTION, buf.write)
		# 	c.perform()
		# 	response_string = buf.getvalue()
		# 	# print response_string
		# 	response = json.loads(response_string)
		# 	# print response
		# 	links = response.get("Response").get("Link")
		# 	for link in links:
		# 		linkid = link.get("LinkId")
		# 		if linkid.startswith("+"):
		# 			linkid = linkid[1:]
		# 		link_val = map_linkID_traffic.get(linkid)
		# 		if link_val is None:
		# 			link_val = {}
		# 			link_val["dynamicSpeedInfo"] = link.get("DynamicSpeedInfo")
		# 			link_val["speedLimit"] = link.get("SpeedLimit")
		# 			map_linkID_traffic[linkid] = link_val

		m = pycurl.CurlMulti()
		reqs = []
		for one_url in array_url:
			response = cStringIO.StringIO()
			handle = pycurl.Curl()
			handle.setopt(pycurl.URL, one_url)
			handle.setopt(pycurl.WRITEFUNCTION, response.write)
			req = (one_url, response, handle)
			m.add_handle(req[2])
			reqs.append(req)
		SELECT_TIMEOUT = 1.0
		num_handles = len(reqs)
		while num_handles:
			ret = m.select(SELECT_TIMEOUT)
			if ret==-1: continue
			while 1:
				ret, num_handles = m.perform()
				if ret != pycurl.E_CALL_MULTI_PERFORM: 
					break
		for req in reqs:
			response_string = req[1].getvalue()
			# print response_string
			response = json.loads(response_string)
			# print response
			links = response.get("Response").get("Link")
			for link in links:
				linkid = link.get("LinkId")
				if linkid.startswith("+"):
					linkid = linkid[1:]
				link_val = map_linkID_traffic.get(linkid)
				if link_val is None:
					link_val = {}
					link_val["dynamicSpeedInfo"] = link.get("DynamicSpeedInfo")
					link_val["speedLimit"] = link.get("SpeedLimit")
					map_linkID_traffic[linkid] = link_val
		return map_linkID_traffic


	def checkAndCacheMapLinkidDetails(self):
		global stdout
		stdout.append("checkAndCacheMapLinkidDetails")

		# check if static gtfs database exists
		# gTFS = GTFS()
		# gtfs_db_name = gTFS.getLatestDBNameFromMongoDB()
		# if gtfs_db_name is None or gtfs_db_name=='':
		# 	request_static_gtfs_data()

		global cached_map_linkID_details
		if len(cached_map_linkID_details.keys())==0 or self.checkCachedMapShouldBeUpdated():
			cached_map_linkID_details = {}
			map_linkID_details = self.sendRequestsToCalculateRoute()
			for key in map_linkID_details.keys():
				cached_map_linkID_details[key] = {}
			db_collection = connection[self.DB_NAME][self.COLLECTION_NAME]
			tpResults = db_collection.find()
			for tpResult in tpResults:
				# print tpResult
				map_tmp = {}
				map_tmp['_id'] = tpResult['_id']
				map_tmp['link'] = tpResult['link']
				map_tmp['traffic_series'] = tpResult['traffic_series']
				if tpResult['link'] is not None and tpResult['traffic_series'] is not None:
					cached_map_linkID_details[tpResult['link']] = map_tmp
		############

		entry_links = self.downloadTrafficForAllLinks()
		array_linkID = entry_links.keys()
		for i in range(0, len(array_linkID)):
			linkID = str(array_linkID[i])
			newTraffic = entry_links[linkID]
			newTraffic['request_time'] = (datetime.datetime.now() - datetime.datetime(1970, 1, 1, 0, 0, 00)).total_seconds()
			if linkID not in cached_map_linkID_details or 'traffic_series' not in cached_map_linkID_details[linkID].keys():
				map_tmp = {}
				map_tmp['link'] = linkID
				map_tmp['traffic_series'] = []
				map_tmp['traffic_series'].append(newTraffic)

				db_collection = connection[self.DB_NAME][self.COLLECTION_NAME]
				_id = db_collection.insert(map_tmp)
				map_tmp['_id'] = _id
				cached_map_linkID_details[linkID] = map_tmp
			else:
				oldTrafficSeries = cached_map_linkID_details[linkID]['traffic_series']
				oldTrafficSpeed = None
				if oldTrafficSeries is not None:
					if 'dynamicSpeedInfo' in oldTrafficSeries[-1] and oldTrafficSeries[-1]['dynamicSpeedInfo'] is not None:
						if 'TrafficSpeed' in oldTrafficSeries[-1]['dynamicSpeedInfo'] and oldTrafficSeries[-1]['dynamicSpeedInfo']['TrafficSpeed'] is not None:
							oldTrafficSpeed = oldTrafficSeries[-1]['dynamicSpeedInfo']['TrafficSpeed']
				newTrafficSpeed = None
				if 'dynamicSpeedInfo' in newTraffic and newTraffic['dynamicSpeedInfo'] is not None:
					if 'TrafficSpeed' in newTraffic['dynamicSpeedInfo'] and newTraffic['dynamicSpeedInfo']['TrafficSpeed'] is not None:
						newTrafficSpeed = newTraffic['dynamicSpeedInfo']['TrafficSpeed']
				if oldTrafficSpeed is not None and newTrafficSpeed is not None:
					if oldTrafficSpeed != newTrafficSpeed:
						oldTrafficSeries.append(newTraffic)
						_id = cached_map_linkID_details[linkID]['_id']
						db_collection = connection[self.DB_NAME][self.COLLECTION_NAME]
						db_collection.update({'_id': _id}, {'$set': {'traffic_series':oldTrafficSeries}})
						# print cached_map_linkID_details[linkID]
					# else:
					# 	print oldTrafficSpeed==newTrafficSpeed
				elif (oldTrafficSpeed is None and newTrafficSpeed is not None) or (oldTrafficSpeed is not None and newTrafficSpeed is None):
					oldTrafficSeries.append(newTraffic)
					_id = cached_map_linkID_details[linkID]['_id']
					db_collection = connection[self.DB_NAME][self.COLLECTION_NAME]
					db_collection.update({'_id': _id}, {'$set': {'traffic_series':oldTrafficSeries}})

		stdout.append("FINISH: request_realtime_traffic_data")
		scheduler.resume_job('request_realtime_traffic_data')

	def requestTrafficForAllRoutes(self):
		global stdout
		if len(stdout)>9999:
			stdout=[]
		stdout.append("START: request_realtime_traffic_data")
		scheduler.pause_job('request_realtime_traffic_data')
		# r = requests.post("https://127.0.0.1:"+str(MY_PORT)+"/scheduler/jobs/request_realtime_traffic_data/pause")
		thread.start_new_thread(self.checkAndCacheMapLinkidDetails, ())
		


class Weather:

	URL_CURRENT_FORECAST = 'https://api.forecast.io/forecast/APIKEY/LATITUDE,LONGITUDE'
	DARKSKYFORECAST_API_KEY = '0af53087a19703cbe61c395d5d30fb3a'
	MAP_COUNTY_COOR = {'DAVIDSON':[36.166683, -86.783300]}
	DB_NAME = 'thub_weather'
	COLLECTION_NAME = 'realtime_data'

	def __init__(self):
		pass

	def downloadWeatherForCounty(self, url):
		r = requests.get(url)
		responseJson = r.json()
		if responseJson is not None:
			document = {}
			document['latitude'] = responseJson['latitude']
			document['longitude'] = responseJson['longitude']
			document['timezone'] = responseJson['timezone']
			document['offset'] = responseJson['offset']
			document['currently'] = responseJson['currently']
			db_collection = connection[self.DB_NAME][self.COLLECTION_NAME]
			db_collection.insert(document)

	def requestWeatherForAllCounty(self):
		print 'START: request_realtime_weather_data'

		for county in self.MAP_COUNTY_COOR.keys():
			coordinate = self.MAP_COUNTY_COOR[county]
			url = self.URL_CURRENT_FORECAST.replace('APIKEY', self.DARKSKYFORECAST_API_KEY)\
				.replace('LATITUDE',str(coordinate[0])).replace('LONGITUDE',str(coordinate[1]))
			thread.start_new_thread(self.downloadWeatherForCounty, (url,))
			

class GTFS:

	URL_TRANSITFEED_GETFEEDVERSIONS = 'http://api.transitfeeds.com/v1/getFeedVersions?feed=nashville-mta%2F220&key=85c02d88-1384-4329-abd7-3925e80735f9'
	# http://api.transitfeeds.com/v1/getFeedVersions?feed=nashville-mta%2F220&key=8924c2c8-a60d-4669-b33b-3d727fb6f4b4
	# http://api.transitfeeds.com/v1/getLatestFeedVersion?feed=nashville-mta%2F220&key=85c02d88-1384-4329-abd7-3925e80735f9

	def __init__(self):
		pass

	# def save_obj(self, obj, name ):
	# 	try:
	# 		with open('tmp/'+ name + '.pkl', 'wb') as f:
	# 			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
	# 			return True;
	# 	except Exception as e:
	# 		print e
	# 		return None

	# def load_obj(self, name ):
	# 	try:
	# 		with open('tmp/' + name + '.pkl', 'rb') as f:
	#         		return pickle.load(f)
	#         except Exception as e:
	#         	print e
	# 		return None

	# download GTFS from url 
	def downloadGTFSfromURL(self, url, feedID):
		try:
			# Check if database already exists
			dbName = feedID.replace("/", "")
			if dbName in connection.database_names():
				return

			# r = self.load_obj(dbName)
			# if r is None:
			# 	r = requests.get(url)
			# 	self.save_obj(r, dbName)
			r = requests.get(url)
			f = StringIO.StringIO() 
			f.write(r.content)
			input_zip = zipfile.ZipFile(f)
			for fileName in input_zip.namelist():
				# print '0852', fileName

				data = StringIO.StringIO(input_zip.read(fileName))
				reader = csv.reader(data)
				
				collectionName = fileName[:-4]
				print collectionName, dbName
				db_collection = connection[dbName][collectionName]
				rowIndex = 0
				header = None
				documents = []
				for row in reader:
					if rowIndex==0:
						header = row
					else:
						document = {}
						for fieldIndex in range(0, len(header)):
							document[header[fieldIndex]] = row[fieldIndex]
						documents.append(document)
					rowIndex+=1
				if len(documents)>0:
					db_collection.insert(documents)
		except Exception as e:
			print "Unexpected error [downloadGTFSfromURL]: ", e

	def getLatestDBNameFromMongoDB(self):
		dbNames = connection.database_names()
		latestDBName = ''
		maxDateName = 0
		for dbName in dbNames:
			if dbName.find('nashville-mta')==-1:
				continue;
			dateName = dbName[16:]
			if maxDateName<int(dateName):
				maxDateName = int(dateName)
				latestDBName = dbName
		return latestDBName

	def requestAllVersions(self, newThreads=True):
		try:
			# r = self.load_obj("feeds")
			# if r is None:
			# 	r = requests.get(self.URL_TRANSITFEED_GETFEEDVERSIONS)
			# 	self.save_obj(r, "feeds")
			r = requests.get(URL_TRANSITFEED_GETFEEDVERSIONS)
			responseJson = r.json()
			if responseJson:
				versions = responseJson['results']['versions']
				for version in versions:
					thread.start_new_thread(self.downloadGTFSfromURL, (version['url'], version['id']))
					
		except Exception as e:
			print "Unexpected error [getFeedVersions]: ", e

	def requestRealtimeGTFSData(self):
		try:
			global stdout
			stdout.append("requestRealtimeGTFSData: Started")
			db = connection.thub_database
			query_time = datetime.datetime.now()
			feed = gtfs_realtime_pb2.FeedMessage()
			vehicledata = urllib.urlopen('http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/vehicle/vehiclepositions.pb')
			feed.ParseFromString(vehicledata.read())
			with open("./vehiclepositions.pb", "wb") as f:
			        f.write(feed.SerializeToString())
			msg = protobuf_to_dict(feed)
			msg['query_time'] = query_time

			db.vehicle_positions.insert(msg);
			# alerts
			feed = gtfs_realtime_pb2.FeedMessage()
			alertdata = urllib.urlopen('http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/alert/alerts.pb')
			feed.ParseFromString(alertdata.read())
			with open("./alerts.pb", "wb") as f:
			        f.write(feed.SerializeToString())
			msg = protobuf_to_dict(feed)
			msg['query_time'] = query_time

			db.alerts.insert(msg)
			#trips
			feed = gtfs_realtime_pb2.FeedMessage()
			tripsdata = urllib.urlopen('http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/tripupdate/tripupdates.pb')
			feed.ParseFromString(tripsdata.read())
			with open("./tripupdates.pb", "wb") as f:
			        f.write(feed.SerializeToString())
			msg = protobuf_to_dict(feed)
			msg['query_time'] = query_time

			db.trip_updates.insert(msg);
			stdout.append("requestRealtimeGTFSData: Finished")
		except Exception as e:
			stdout.append("requestRealtimeGTFSDataError")
			stdout.append(e)
			print "Unexpected error [requestRealtimeData]: ", e


	