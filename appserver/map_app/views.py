from dis import dis
from time import time
from urllib import response
from venv import create
from django.shortcuts import render
from django.http import HttpResponse
import json
import hashlib
import datetime
#from conda import CondaError
from numpy import integer, polymul

from sqlalchemy import false
from more_itertools import first
from requests import request
from sympy import re
# Create your views here.
from .models import Users, Connections, Logs

#API:all

def all(request):
	result = 'ok'
	from .models import Connections, Users
	offline_connection_with_pid = Connections.objects.filter(status='offline')
	online_connection_with_pid = Connections.objects.filter(status='online')

	offline_pid = [(data.user_id1.prefecture_id, data.user_id2.prefecture_id) for data in offline_connection_with_pid]
	online_pid = [(data.user_id1.prefecture_id, data.user_id2.prefecture_id) for data in online_connection_with_pid]

	offline_connections = [[0 for j in range(47)] for i in range(47)]
	online_connections = [[0 for j in range(47)] for i in range(47)]
	for id1, id2 in offline_pid:
		offline_connections[id1][id2] += 1
	for id1, id2 in online_pid:
		online_connections[id1][id2] += 1

	#各都道府県のユーザ数を求める処理
	from django.db.models import Count
	users_num = [0 for i in range(47)]
	#prefecture_idでGroupByを行い,Count(prefecture_id)を実行
	rows = Users.objects.values('prefecture_id').annotate(total = Count('prefecture_id'))
	for row in rows:
		pid = row['prefecture_id']
		num = row['total']
		users_num[pid] = num

	#つながりの個数をN*Mで割る処理
	for i in range(47):
		for j in range(47):
			M = users_num[i]
			N = users_num[j]
			offline_connections[i][j] /= (N * M)
			online_connections[i][j] /= (N * M)

	response = {"offline_connections": offline_connections, "online_connections": online_connections}
	json_response = json.dumps(response, ensure_ascii=False, indent=2)
	return HttpResponse(json_response)


#API:signup
def signup(request):
	req = json.loads(request.body)
	point = 0
	try:	# if exist same id
		Users.objects.get(user_id=req['userId'])
		result = {'status': 400}
	except:	# create new user
		Users.objects.create(user_id=req['userId'],
			user_name=req['userName'], prefecture_id=req['prefectureId'], point = point)
		result = {'status': 200}
	return HttpResponse(json.dumps(result))

#API:signin
def signin(request):
	req = json.loads(request.body)
	try:	# if exist user_id
		Users.objects.get(user_id=req['userId'])
		result = {'status': 200}
	except:	# user_id not found
		result = {'status': 400}
	return HttpResponse(json.dumps(result))

#API:connection
def connection(request):
	from .models import Connections,Users
	request = json.loads(request.body)
	UserId1 = request["userId1"]
	UserId2 = request["userId2"]
	status = request["status"]
	mkHash1 = UserId1 + UserId2 + status
	mkHash2 = UserId2 + UserId1 + status
	hs1 = str(hashlib.md5(mkHash1.encode()).hexdigest())
	hs2 = str(hashlib.md5(mkHash2.encode()).hexdigest())
	User1 = Users.objects.get(pk=UserId1)
	User2 = Users.objects.get(pk=UserId2)
	# connectionMileageテスト用データ(サーバーからデータを取得する処理を実装する)
	frequency = 0
	DIFF_JST_FROM_UTC = 9
	today = datetime.datetime.now() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
	distance = abs(User1.prefecture_id - User2.prefecture_id)
	try:
		frequency = Connections.objects.get(pk=hs1).times
	except:
		frequency = 0
	point = connectionMileage(request,status,frequency,distance)
	log_point = point
	result = {
		"hash1":hs1,
		"hash2":hs2,
		"userId1":UserId1,
		"userId2":UserId2,
		"status":status,
		"distance":distance,
		"point":point,
		"freq":frequency,
	}
	try:
		# frequency != 0: # if exist connection_id
		Connections.objects.get(connection_id=hs1)
		point = Connections.objects.get(connection_id=hs1).point + point
		createDay = Connections.objects.get(connection_id=hs1).created_by
		saveConnection(hs1,hs2,UserId1,UserId2,status,createDay,today,point,frequency)
		savepoint(UserId1,UserId2,point)
	except: # register to Connections
		saveConnection(hs1,hs2,UserId1,UserId2,status,today,today,point,frequency)
		savepoint(UserId1,UserId2,point)


	rows = Connections.objects.filter(user_id1=UserId1, user_id2=UserId2)
	timeList = []
	for row in rows:
		timeList.append(row.created_by)
	log_createTime = min(timeList)
	logHash1 = UserId1 + UserId2 + str(today)
	logHash2 = UserId2 + UserId1 + str(today)
	log_hs1 = str(hashlib.md5(logHash1.encode()).hexdigest())
	log_hs2 = str(hashlib.md5(logHash2.encode()).hexdigest())
	Logs.objects.create(connection_id=log_hs1, user_id1=User1, user_id2=User2, status=status, point=log_point, times=0, created_by=log_createTime, updated_by=today)
	Logs.objects.create(connection_id=log_hs2, user_id1=User2, user_id2=User1, status=status, point=log_point, times=0, created_by=log_createTime, updated_by=today)
	return HttpResponse(json.dumps(result))

#API:userByPrefecture
#都道府県ごとのユーザ情報を表示
def userByPrefecture(request):
	request = json.loads(request.body)
	prefectureId = request['prefectureId']
	rows = Users.objects.filter(prefecture_id=prefectureId)
	users = [{"userId":row.user_id, "userName":row.user_name, "prefectureId": row.prefecture_id} for row in rows]
	response = {"users": users}
	return HttpResponse(json.dumps(response, ensure_ascii=False))

#API:connectionByUser
#ユーザごとのつながりを表示
def connectionByUser(request):
	request = json.loads(request.body)
	userId = request['userId']

	from .models import Connections
	rows = Connections.objects.filter(user_id1 = userId)

	offline_connections_detail = [[] for i in range(47)]
	online_connections_detail = [[] for i in range(47)]

	offline_connections = [0 for i in range(47)]
	online_connections = [0 for i in range(47)]

	for row in rows:
		userId2 = row.user_id2.user_id
		userName = row.user_id2.user_name
		prefectureId = row.user_id2.prefecture_id
		createdBy = str(row.created_by)#DATETIME -> str
		updatedBy = str(row.updated_by)#DATETIME -> str
		point = row.point
		print(userId2, userName, prefectureId)

		if(row.status == "offline"):
			offline_connections_detail[prefectureId].append({"userId": userId2, "userName": userName, "createdBy": createdBy, "updatedBy": updatedBy, "point": point})
			offline_connections[prefectureId] += 1

		if(row.status == "online"):
			online_connections_detail[prefectureId].append({"userId": userId2, "userName": userName, "createdBy": createdBy, "updatedBy": updatedBy, "point": point})
			online_connections[prefectureId] += 1

	#各都道府県のユーザ数を求める処理
	from django.db.models import Count
	users_num = [0 for i in range(47)]

	#prefecture_idでGroupByを行い,Count(prefecture_id)を実行
	rows = Users.objects.values('prefecture_id').annotate(total = Count('prefecture_id'))
	for row in rows:
		pid = row['prefecture_id']
		num = row['total']
		users_num[pid] = num

	#各都道府県に住むユーザ数Nで割る処理
	for i in range(47):
		N = users_num[i]
		offline_connections[i] /= N
		online_connections[i] /= N

	response = {"offline_connections":offline_connections, "online_connections":online_connections,  "offline_connections_detail": offline_connections_detail, "online_connections_detail": online_connections_detail}
	return HttpResponse(json.dumps(response, ensure_ascii=False))

def searchUser(request):
	request = json.loads(request.body)
	if 'userIdKey' in request:
		userIdKey = request['userIdKey']
	else:
		userIdKey = ''
	if 'userNameKey' in request:
		userNameKey = request['userNameKey']
	else:
		userNameKey = ''
	if 'prefectureId' in request:
		prefectureId = request['prefectureId']
	else:
		prefectureId = ''

	rows = Users.objects.filter(user_id__icontains=userIdKey, user_name__icontains=userNameKey, prefecture_id__icontains=prefectureId)
	users = [{"userId":row.user_id, "userName":row.user_name, "prefectureId": row.prefecture_id, "point": row.point} for row in rows]
	response = {"users": users}
	return HttpResponse(json.dumps(response, ensure_ascii=False))

def searchUserByUserIdExactly(request):
	request = json.loads(request.body)
	if 'userIdKey' in request:
		userIdKey = request['userIdKey']
	else:
		userIdKey = ''
	rows = Users.objects.filter(user_id__iexact=userIdKey)
	users = [{"userId":row.user_id, "userName":row.user_name, "prefectureId": row.prefecture_id, "point": row.point} for row in rows]
	response = {"users": users}
	return HttpResponse(json.dumps(response, ensure_ascii=False))

def searchConnection(request):
	request = json.loads(request.body)
	if 'userId1Key' in request:
		userId1Key = request['userId1Key']
	else:
		userId1Key = ''
	if 'userId2Key' in request:
		userId2Key = request['userId2Key']
	else:
		userId2Key = ''
	if 'pointGreaterThan' in request:
		pointGreaterThan = request['pointGreaterThan']
	else:
		pointGreaterThan = 0
	if 'pointLessThan' in request:
		pointLessThan = request['pointLessThan']
	else:
		pointLessThan = 1000000

	#[TODO]時間での絞り込み（直近１週間、1ヶ月など）
	if(userId1Key != '' and userId2Key != ''):
		rows = Connections.objects.filter(user_id1__user_id__iexact=userId1Key, user_id2__user_id__iexact=userId2Key, point__gt=pointGreaterThan, point__lt = pointLessThan)
	if(userId1Key != '' and userId2Key == ''):
		rows = Connections.objects.filter(user_id1__user_id__iexact=userId1Key, point__gt=pointGreaterThan, point__lt = pointLessThan)
	if(userId1Key == '' and userId2Key == ''):
		rows = Connections.objects.filter(point__gt=pointGreaterThan, point__lt = pointLessThan)

	connections = [{"connectionId": row.connection_id, "userId1":row.user_id1.user_id, "userId2":row.user_id2.user_id, "createdBy": str(row.created_by), "updatedBy": str(row.updated_by), "point": row.point} for row in rows]
	response = {"connections": connections}
	return HttpResponse(json.dumps(response, ensure_ascii=False))

# 適当に計算式を実装
# Connection Mileage
def connectionMileage(request,status,frequency,distance):
	# jsonから必要なデータを取得し計算に最適化する処理を記述
	UserId1 = request["userId1"]
	UserId2 = request["userId2"]
	# UserIdから距離や最終connectionを取得
	UserId1 = Users.objects.get(user_id=UserId1)
	UserId2 = Users.objects.get(user_id=UserId2)
	basePt = 10
	statusPt = 0
	firstBonusPt = 0
	frequencyPt = 3
	distancePt = 1
	if status == "offline":
		statusPt = 5
	if frequency == 0:
		firstBonusPt = 5
	elif frequency > 5:
		frequency *= 2
	distance = int(distance/2)
	if distance > 11:
		distancePt = 3
	elif distance > 7:
		distancePt = 2
	elif distance > 3:
		distancePt = 1
	point = basePt + statusPt + frequencyPt + firstBonusPt + distancePt
	return(point)

def saveConnection(hs1,hs2,UserId1,UserId2,status,createDay,today,point,frequency):
	UserId1 = Users.objects.get(user_id=UserId1)
	UserId2 = Users.objects.get(user_id=UserId2)
	SaveConnectionData1 = Connections(connection_id=hs1, user_id1=UserId1, user_id2=UserId2, status=status, point=point, times=frequency + 1, created_by=createDay, updated_by=today)
	SaveConnectionData2 = Connections(connection_id=hs2, user_id1=UserId2, user_id2=UserId1, status=status, point=point, times=frequency + 1, created_by=createDay, updated_by=today)
	SaveConnectionData1.save()
	SaveConnectionData2.save()
	return()

def savepoint(UserId1,UserId2,point):
	User1 = Users.objects.get(user_id=UserId1)
	User2 = Users.objects.get(user_id=UserId2)
	SaveUserPt1 = Users(user_id=UserId1, user_name=User1.user_name, prefecture_id=User1.prefecture_id, point=User1.point + point)
	SaveUserPt2 = Users(user_id=UserId2, user_name=User2.user_name, prefecture_id=User2.prefecture_id, point=User2.point + point)
	SaveUserPt1.save()
	SaveUserPt2.save()
	return()

def ranking(request):
	UPPER_SLICE = 10
	table = Users.objects.exclude(point=0)
	users = [{"userId":user.user_id, "userName":user.user_name, "prefectureId": user.prefecture_id, "point": user.point} for user in table]
	ranking = sorted(users, key=lambda x:x['point'], reverse=True)
	return HttpResponse(json.dumps({"ranking":ranking[:UPPER_SLICE]}, ensure_ascii=False))

def log(request):
	req = json.loads(request.body)
	offline_log = [[] for i in range(47)]
	online_log = [[] for i in range(47)]
	rows = Logs.objects.filter(user_id1=req['userId'])
	for row in rows:
		userId2 = row.user_id2.user_id
		userName = row.user_id2.user_name
		prefectureId = row.user_id2.prefecture_id
		createdBy = str(row.created_by)#DATETIME -> str
		updatedBy = str(row.updated_by)#DATETIME -> str
		point = row.point

		if(row.status == "offline"):
			offline_log[prefectureId].append({"userId": userId2, "userName": userName, "createdBy": createdBy, "updatedBy": updatedBy, "point": point})

		if(row.status == "online"):
			online_log[prefectureId].append({"userId": userId2, "userName": userName, "createdBy": createdBy, "updatedBy": updatedBy, "point": point})
	response = {"offline_log":offline_log, "online_log":online_log}
	return HttpResponse(json.dumps(response, ensure_ascii=False))
