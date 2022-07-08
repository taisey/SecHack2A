from django.urls import path
from . import views

urlpatterns = [
	#APIのpathを設定する（path, views.api名, name?）
	path('registerEmotion', views.registerEmotion, name='registerEmotion'),
	path('summarizeEmotion', views.summarizeEmotion, name='summarizeEmotion'),
	path('student', views.student, name='student'),
	path('teacher', views.teacher, name='teacher'),
]
