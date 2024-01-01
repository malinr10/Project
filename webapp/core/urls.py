from django.urls import path
from . import views

urlpatterns = [
   path('login', views.login, name='login'),
   path('register', views.register, name='register'),
   path('logout', views.logout, name='logout'),
   path('profile', views.profile, name='profile'),
   path('settings', views.settings, name='settings'),
   path('update_akun', views.update_akun, name='update_akun'),
   path('home', views.homePage, name='home'),
   path('upload_image', views.upload_image, name='upload_image'),
   path('update_image/<uuid:post_id>/edit/', views.update_image, name='update_image'),
   path('delete_image/<uuid:post_id>/', views.delete_image, name='delete_image'),
   path('like_post', views.like_post, name='like_post'),
   path('download_images/<uuid:post_id>/', views.download_images, name='download_images'),
   path('download_video/<uuid:video_id>/', views.download_video, name='download_video'),
   path('', views.landing, name="landing"),
   path('upload_video', views.upload_video, name='upload_video'),
   path('update_video/<uuid:video_id>/edit/', views.update_video, name='update_video'),
   path('delete_video/<uuid:video_id>/', views.delete_video, name='delete_video'),
   path('like_video', views.like_video, name='like_video'),
   path('upload_modul', views.upload_modul, name='upload_modul'),
   path('update_modul/<uuid:modul_id>/edit/', views.update_modul, name='update_modul'),
   path('delete_modul/<uuid:modul_id>/', views.delete_modul, name='delete_modul'),
   path('like_modul', views.like_modul, name='like_modul'),
   path('search_konten', views.search_konten, name='search_konten'),
   path('detail/<uuid:id>/', views.detail, name='detail'),
   path('update_password', views.update_password, name='update_password'),
   path('image', views.view_image, name='view_image'),
   path('video', views.view_video, name='view_video'),
   path('modul', views.view_modul, name='view_modul'),

   
]