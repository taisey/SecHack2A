from django.urls import path
from . import views

urlpatterns = [
	#APIのpathを設定する（path, views.api名, name?）
	path('connection', views.connection, name='connection'),
	path('all', views.all, name='all'),
	path('signup', views.signup, name='signup'),
	path('signin', views.signin, name='signin'),
	path('userByPrefecture', views.userByPrefecture, name= 'userByPrefecture'),
	path('connectionByUser', views.connectionByUser, name = 'connectionByUser'),
	path('searchUser', views.searchUser, name = 'searchUser'),
	path('searchUserByUserIdExactly', views.searchUserByUserIdExactly, name = 'searchUserByUserIdExactly'),
	path('searchConnection', views.searchConnection, name = 'searchConnection'),
	path('ranking', views.ranking, name = 'ranking'),
	path('log', views.log, name = 'log'),
]
