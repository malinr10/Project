from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()

# Create your models here.

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    profile_image = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    alamat = models.TextField(blank=True)
    tanggal_lahir = models.DateField(blank=True, null=True)
    nama_lengkap = models.CharField(max_length=100, blank=True)
    no_hp = models.CharField(max_length=20, blank=True)
    jenis_kelamin = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.user.username

class Post(models.Model):
    id_post = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kategori_id = models.ForeignKey('Kategori', on_delete=models.CASCADE)
    lisensi_id = models.ForeignKey('Lisensi', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    judul = models.CharField(max_length=100)
    deskripsi = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='post_thumbnail', null=True)
    created_at = models.DateTimeField(default=datetime.now)
    no_of_like = models.IntegerField(default=0)
    
    def __str__(self):
        return self.judul

class PostImage(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images', null=True)

    def __str__(self):
        return self.post.judul

class PostVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kategori_id = models.ForeignKey('Kategori', on_delete=models.CASCADE)
    lisensi_id = models.ForeignKey('Lisensi', on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='post_thumbnail', null=True)
    file_video = models.FileField(upload_to='post_videos', null=True)
    link_video = models.CharField(max_length=255, null=True)
    judul = models.CharField(max_length=100)
    deskripsi = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    no_of_like = models.IntegerField(default=0)
    
    def __str__(self):
        return self.judul

class PostModul(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kategori_id = models.ForeignKey('Kategori', on_delete=models.CASCADE)
    lisensi_id = models.ForeignKey('Lisensi', on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='post_thumbnail', null=True)
    file_modul = models.FileField(upload_to='post_moduls', null=True)
    judul = models.CharField(max_length=100)
    deskripsi = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    no_of_like = models.IntegerField(default=0)
    
    def __str__(self):
        return self.judul

# class PostAudio(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     kategori_id = models.ForeignKey('Kategori', on_delete=models.CASCADE)
#     lisensi_id = models.ForeignKey('Lisensi', on_delete=models.CASCADE)
#     thumbnail = models.ImageField(upload_to='post_thumbnail', null=True)
#     file_audio = models.FileField(upload_to='post_audios', null=True)
#     judul = models.CharField(max_length=100)
#     deskripsi = models.TextField()
#     created_at = models.DateTimeField(default=datetime.now)
#     no_of_like = models.IntegerField(default=0)
    
#     def __str__(self):
#         return self.judul

class Kategori(models.Model):
    nama_kategori = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nama_kategori

class Lisensi(models.Model):
    nama_lisensi = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nama_lisensi

class LikePost(models.Model):
    post_id = models.CharField(max_length=500, null=True)
    video_id = models.CharField(max_length=500, null=True)
    modul_id = models.CharField(max_length=500, null=True)
    audio_id = models.CharField(max_length=500, null=True)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username