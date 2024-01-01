from django.contrib import admin
from .models import Profile, Post, LikePost, Lisensi, Kategori, PostVideo, PostImage, PostModul

# Register your models here.
#last coding
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(LikePost)
admin.site.register(Lisensi)
admin.site.register(Kategori)
admin.site.register(PostVideo)
admin.site.register(PostImage)
admin.site.register(PostModul)