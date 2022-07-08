from django.shortcuts import render
from django.http import HttpResponse
from .models import Users
import json
import datetime

def currentDateTime():
	DIFF_JST_FROM_UTC = 9
	return datetime.datetime.now() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)

def beforeDateTime(seconds):
	current = currentDateTime()
	dt = datetime.timedelta(seconds=seconds)
	return current - dt


def updateEmotionInfo(request):
	request = json.loads(request.body)
	userId = request['userId']
	angry = request['angry']
	disgusted = request['disgusted']
	fearful = request['fearful']
	happy = request['happy']
	neutral = request['neutral']
	surprised = request['surprised']
	sad = request['sad']
	createdBy = currentDateTime()

	# #createdByを除く情報を挿入or更新
	# obj, created = Users.objects.update_or_create(user_id=userId, angry=angry, disgusted=disgusted, fearful=fearful,
	# 	happy=happy, neutral=neutral, surprised=surprised,
	# 	defaults={'angry':angry, 'disgusted':disgusted, 'sad':sad, 'fearful':fearful, 'happy':happy, 'neutral':neutral, 'surprised':surprised, 'createdby':createdBy})

	if not(Users.objects.filter(user_id=userId).exists()):
		Users.objects.create(user_id=userId, angry=angry, disgusted=disgusted, fearful=fearful,
		happy=happy, neutral=neutral, surprised=surprised, sad = sad, createdby=createdBy)
	else:		
	#createdByを挿入
		row = Users.objects.get(user_id=userId)
		row.angry = angry
		row.happy = happy
		row.surprised = surprised
		row.fearful = fearful
		row.neutral = neutral
		row.disgusted = disgusted
		row.sad = sad
		row.createdby = createdBy
		row.save()

	return 1

def student(request):
	return render(request, 'student/index.html')

def teacher(request):
	return render(request, 'teacher/index.html')
	
# Create your views here.
def registerEmotion(request):
	updateEmotionInfo(request)
	result = {'status': 200}
	return HttpResponse(json.dumps(result))

def summarizeEmotion(request):

	#5秒前の時刻
	floor_time = beforeDateTime(5)
	#rows = Users.objects.filter(createdby__lte=floor_time)
	rows = Users.objects.filter()
	emotion_list = {'num':0, 'angry':0, 'disgusted':0, 'sad':0, 'fearful':0, 'happy':0, 'neutral':0, 'surprised':0}
	for row in rows:
		emotion_list['num']+= 1
		emotion_list['angry'] += row.angry
		emotion_list['disgusted'] += row.disgusted
		emotion_list['sad'] += row.sad
		emotion_list['fearful'] += row.fearful
		emotion_list['happy'] += row.happy
		emotion_list['neutral'] += row.neutral
		emotion_list['surprised'] += row.surprised
	for key in emotion_list.keys():
		if key != 'num':
			num = emotion_list['num']
			emotion_list[key] /= num
	#result = {'status': 200}
	return HttpResponse(json.dumps(emotion_list))