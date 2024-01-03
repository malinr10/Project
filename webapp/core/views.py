from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User, auth
from .models import Profile, Post, LikePost, Kategori, Lisensi, PostImage, PostVideo, PostModul
from urllib.parse import urlparse, parse_qs
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseRedirect
import os
from django.conf import settings
import zipfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import mimetypes
import pandas as pd
import numpy as np

# Landing Page
def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return render(request, 'index.html')
# End of Landing Page

# Create your views here.

#Start of User Authentication
def register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password= request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username already taken', extra_tags='form_register')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken', extra_tags='form_register')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save();
                
                #Log User and Direct to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                
                #create profile object for new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password tidak sama', extra_tags='form_register')
            return redirect('register')
    else:
        return render(request, 'register.html')
    
def login(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username']
        password= request.POST['password']
        
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Invalid Credentials', extra_tags='form_login')
            return redirect('login')
    else:
        return render(request, 'login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')
#End of User Authentication

#Start of User Interface

#Start of Home 
def bubble_sort(posts):
    post = Post.objects.all()
    video = PostVideo.objects.all()
    modul = PostModul.objects.all()
    posts = list(post) + list(video) + list(modul)
    n = len(posts)

    for i in range(n):
        for j in range(0, n - i - 1):
            # Ganti 'created_at' dengan atribut atau metode yang sesuai untuk objek Post, Video, atau Modul
            if posts[j].created_at < posts[j + 1].created_at:
                posts[j], posts[j + 1] = posts[j + 1], posts[j]

    return posts

@login_required(login_url='login')
def homePage(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    post = Post.objects.all()
    video = PostVideo.objects.all()
    modul = PostModul.objects.all()
    images = PostImage.objects.filter(post__in=post)
    lisensi = Lisensi.objects.all()

    all_posts = list(post) + list(video) + list(modul)

    sorted_posts = bubble_sort(all_posts)

    latest_posts = sorted_posts[:5]

    sort_option = request.GET.get('sort', 'latest') 
    if sort_option == 'latest':
        post = Post.objects.all().order_by('-created_at')
        video = PostVideo.objects.all().order_by('-created_at')
        modul = PostModul.objects.all().order_by('-created_at')
    elif sort_option == 'most_liked':
        post = Post.objects.all().order_by('-no_of_like')
        video = PostVideo.objects.all().order_by('-no_of_like')
        modul = PostModul.objects.all().order_by('-no_of_like')
    
    

    return render(request, 'homepage.html', {'post': post, 'profile': profile, 'images': images, 'lisensi': lisensi, 'video': video, 'modul': modul, 'latest_posts': latest_posts})
#End of Home Page

#Start of CRUD 

#Detail Image
def detail(request, id):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    lisensi = Lisensi.objects.all()
    post = Post.objects.get(id_post=id)
    photos = PostImage.objects.filter(post=post)
    return render(request, 'detail/detail.html', {'post': post, 'photos': photos, 'profile': profile, 'lisensi': lisensi})
#End of Detail Image

#Start of Download Image
def download_images(request, post_id):
    post = Post.objects.get(id_post=post_id)
    photos = PostImage.objects.filter(post=post)

    # Membuat objek response
    response = HttpResponse(content_type='application/zip')
    zip_filename = f'post_{post.judul}_images.zip'

    # Membuat objek zip
    with zipfile.ZipFile(response, 'w') as zip_file:
        for photo in photos:
            image_path = photo.image.path
            zip_file.write(image_path, os.path.basename(image_path))

    # Menentukan nama file ZIP yang akan diunduh
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'

    return response
#End of Download Image

#Start of Upload Image
@login_required(login_url='login')
def upload_image(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        images = request.FILES.getlist('images')
        thumbnail = request.FILES['thumbnail']
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        allowed_formats = ['image/jpeg', 'image/png', 'image/jpg']

        if thumbnail.content_type not in allowed_formats:
            messages.error(request, f'Format File Tidak Sesuai!!!, Gunakan Format .jpg, .jpeg, dan .png: {thumbnail.name}', extra_tags='form_upload_image')

        new_post = Post.objects.create(user=user, judul=judul, deskripsi=deskripsi, kategori_id=kategori_instance, lisensi_id=lisensi_instance, thumbnail=thumbnail) 

        for image in images:
            if image.content_type not in allowed_formats:
                messages.error(request, f'Format File Tidak Sesuai!!!, Gunakan Format .jpg, .jpeg, dan .png: {image.name}', extra_tags='form_upload_image')
            else:
                PostImage.objects.create(post=new_post, image=image)

        messages.success(request, 'Konten Berhasil Diupload', extra_tags='form_upload_image')

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'upload/upload_image.html', {'kategori': kategori, 'lisensi': lisensi, 'profile': profile})
#End Of Upload Image

#Start of Update Image
def update_image(request, post_id):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()
    post = Post.objects.get(id_post=post_id)
    postImage = Post.objects.get(id_post=post_id)
    images = PostImage.objects.filter(post=post)

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']
        images = request.FILES.getlist('images')

        if request.FILES.get('thumbnail') == None:
            post.thumbnail = post.thumbnail
        elif request.FILES.get('thumbnail') != None:
            post.thumbnail = request.FILES['thumbnail']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        post.judul = judul
        post.deskripsi = deskripsi
        post.kategori_id = kategori_instance
        post.lisensi_id = lisensi_instance
        post.save()

        for image in images:
            if image == None:
                image.image = image
            elif image != None:
                if image == images[0]:
                    PostImage.objects.filter(post=post).delete()
                PostImage.objects.create(post=post, image=image)
        
        messages.success(request, 'Konten Berhasil Diupdate', extra_tags='form_update_image')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'update/update_image.html', {'post': post, 'images': images, 'kategori': kategori, 'lisensi': lisensi, 'postImage': postImage, 'profile': profile})
#END of Update Image

#Start of Delete Image
def delete_image(request, post_id):
    post = Post.objects.get(id_post=post_id)

    if request.method == 'POST':
        # Delete all images associated with the post
        images = PostImage.objects.filter(post=post)
        for image in images:
            if image.image:
                # Adjust the folder structure based on your media root and upload_to settings
                os.remove(image.image.path)
            # Delete the post itself
        if post.thumbnail:
            os.remove(post.thumbnail.path)
        images.delete()
        post.delete()

        messages.success(request, 'Konten Berhasil Dihapus!')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])  # Redirect to the home page after deletion
    else:
        # Handle GET request, render confirmation page
        return render(request, 'profile', {'post': post})
#END of Delete 

#start of view image
def view_image(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    posts = Post.objects.all()

    post_df = pd.DataFrame.from_records(posts.values())

    if Post.objects.all().exists():
        sort_option = request.GET.get('sort', 'latest') 
        if sort_option == 'latest':
            post_df = post_df.sort_values(by='created_at', ascending=False)
        elif sort_option == 'most_liked':
            post_df = post_df.sort_values(by='no_of_like', ascending=False)
        
        sorted_post_ids = post_df['id_post'].tolist()
        post = sorted(posts, key=lambda x: sorted_post_ids.index(x.id_post))

        return render(request, 'konten/gambar.html', {'post': post, 'profile': profile})
    else:
        return render(request, 'konten/gambar.html', {'profile': profile})
#end of view image

#start of like image post
def like_post(request):
    referring_url = request.META.get('HTTP_REFERER')
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id_post=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_like += 1
        post.save()
        return redirect(referring_url)
    else:
        like_filter.delete()
        post.no_of_like -= 1
        post.save()
        return redirect(referring_url)
#end of like image post

#End of CRUD Image

#Start of Setting Profile
@login_required(login_url='login')
def settings(request):
    if request.method == 'POST':
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        
        #update profile
        if request.FILES.get('profile_image') == None:
            profile.profile_image = profile.profile_image
        elif request.FILES.get('profile_image') != None:
            profile.profile_image = request.FILES['profile_image']

        profile.alamat = request.POST['alamat']
        profile.tanggal_lahir = request.POST['tanggal_lahir']
        profile.nama_lengkap = request.POST['nama_lengkap']
        profile.no_hp = request.POST['no_hp']
        profile.jenis_kelamin = request.POST['jenis_kelamin']
        profile.save()

        messages.success(request, 'Profile Berhasil Diupdate!', extra_tags='form_profile')
        
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        context = {
            'profile': profile,
        }
        return render(request, 'setting.html', context)
    
def hitungJumlahLike():
    post_likes = np.array(Post.objects.values_list('no_of_like', flat=True))
    modul_likes = np.array(PostModul.objects.values_list('no_of_like', flat=True))
    video_likes = np.array(PostVideo.objects.values_list('no_of_like', flat=True))

    all_likes = np.concatenate([post_likes, modul_likes, video_likes])

    sum_likes = np.sum(all_likes)

    return sum_likes


@login_required(login_url='login')
def profile(request):
    if request.method == 'POST':
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        #update profile
        
        if request.FILES.get('profile_image') == None:
            profile.profile_image = profile.profile_image
        elif request.FILES.get('profile_image') != None:
            profile.profile_image = request.FILES['profile_image']
        
        profile.alamat = request.POST['alamat']
        profile.tanggal_lahir = request.POST['tanggal_lahir']
        profile.nama_lengkap = request.POST['nama_lengkap']
        profile.no_hp = request.POST['no_hp']
        profile.jenis_kelamin = request.POST['jenis_kelamin']
        profile.save()
        
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        jumlah_likes = hitungJumlahLike()
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        post = Post.objects.filter(user=user)
        video = PostVideo.objects.filter(user=user)
        images = PostImage.objects.filter(post__in=post)
        modul = PostModul.objects.filter(user=user)
        context = {
            'profile': profile,
            'post': post,
            'images': images,
            'video': video,
            'modul': modul,
            'jumlah_likes': jumlah_likes,
        }
        return render(request, 'profile.html', context)

@login_required(login_url='login')
def update_akun(request):
    if request.method == 'POST':
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        
        #update user
        user_model.username = request.POST['username']
        user_model.email = request.POST['email']
        user_model.save()
        
        messages.success(request, 'Akun Berhasil Diupdate!', extra_tags='form_akun')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('settings')
    
@login_required(login_url='login')
def update_password(request):
    if request.method == 'POST':
        user = request.user
        user_model = User.objects.get(username=user)
        
        #update password
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_new_password = request.POST['confirm_new_password']
         # Verifikasi password lama
        if not request.user.check_password(old_password):
            messages.error(request, 'Password lama tidak benar.', extra_tags="form_password")
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        # Verifikasi konfirmasi password baru
        if new_password != confirm_new_password:
            messages.error(request, 'Konfirmasi password baru tidak cocok.', extra_tags="form_password")
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        # Set password baru dan perbarui session auth hash
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password Berhasil Diupdate!', extra_tags="form_password")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('settings')

#CRUD VIDEO

# Fungsi ini digunakan untuk mendapatkan ID video YouTube dari URL tautan YouTube.
def get_youtube_video_id(url):
    """
    Fungsi ini digunakan untuk mendapatkan ID video YouTube dari URL tautan YouTube.
    """
    query = urlparse(url)
    if query.hostname == 'www.youtube.com' or query.hostname == 'youtube.com':
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        elif query.path[:3] == '/v/':
            return query.path.split('/')[2]
    elif query.hostname == 'youtu.be':
        return query.path[1:]
    return None

#start of upload_video
def upload_video(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        file_video = request.FILES.get('file_video')
        link_video = request.POST.get('link_video')
        thumbnail = request.FILES.get('thumbnail')
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        allowed_formats = ['video/mp4', 'video/avi', 'video/mkv']

        if file_video and file_video.content_type not in allowed_formats:
            messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .mp4, .avi, dan .mkv: {file_video.name}', extra_tags='form_upload_video')
        elif not file_video and not link_video:
            messages.error(request, 'Harap unggah file video atau masukkan tautan YouTube.', extra_tags='form_upload_video')
        else:
            # Jika pengguna mengunggah melalui tautan YouTube
            if link_video:
                youtube_video_id = get_youtube_video_id(link_video)
                if youtube_video_id:
                    # Lakukan sesuatu dengan ID video YouTube (mis. simpan di database)
                    # Misalnya, Anda dapat menyimpan ID video YouTube bersama dengan data lainnya di model PostVideo.
                    new_post = PostVideo.objects.create(
                        user=user,
                        judul=judul,
                        deskripsi=deskripsi,
                        kategori_id=kategori_instance,
                        lisensi_id=lisensi_instance,
                        thumbnail=thumbnail,
                        link_video=youtube_video_id,
                        # file_video tidak diisi karena ini dari tautan YouTube
                    )
                    messages.success(request, 'Konten Berhasil Diupload', extra_tags='form_upload_video')
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])
                else:
                    messages.error(request, 'Tautan YouTube tidak valid.', extra_tags='form_upload_video')
            else:
                # Jika pengguna mengunggah file video
                new_post = PostVideo.objects.create(
                    user=user,
                    judul=judul,
                    deskripsi=deskripsi,
                    kategori_id=kategori_instance,
                    lisensi_id=lisensi_instance,
                    thumbnail=thumbnail,
                    link_video=link_video,
                    file_video=file_video,
                )
                messages.success(request, 'Konten Berhasil Diupload', extra_tags='form_upload_video')
                return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, 'upload/upload_video.html', {'kategori': kategori, 'lisensi': lisensi, 'profile': profile})
#end of upload_video

#start of update_video
def update_video(request, video_id):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()
    video = PostVideo.objects.get(id=video_id)

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']
        file_video = request.FILES.get('file_video')
        link_video = request.POST.get('link_video')

        if request.FILES.get('thumbnail') == None:
            video.thumbnail = video.thumbnail
        elif request.FILES.get('thumbnail') != None:
            video.thumbnail = request.FILES['thumbnail']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        video.judul = judul
        video.deskripsi = deskripsi
        video.kategori_id = kategori_instance
        video.lisensi_id = lisensi_instance
        video.save()

        if file_video:
            allowed_formats = ['video/mp4', 'video/avi']
            if file_video.content_type not in allowed_formats:
                messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .mp4, .avi, dan .mkv: {file_video.name}', extra_tags='form_update_video')
            else:
                video.file_video = file_video
                video.link_video = None
                video.save()
        elif link_video:
            youtube_video_id = get_youtube_video_id(link_video)
            if youtube_video_id:
                video.file_video = None
                video.link_video = youtube_video_id
                video.save()
            else:
                messages.error(request, 'Tautan YouTube tidak valid.', extra_tags='form_update_video')

        messages.success(request, 'Konten Berhasil Diupdate', extra_tags='form_update_video')    
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'update/update_video.html', {'video': video, 'kategori': kategori, 'lisensi': lisensi, 'profile': profile})
#end of update_video

#start of delete_video
def delete_video(request, video_id):
    video = PostVideo.objects.get(id=video_id)

    if request.method == 'POST':
        try:
            fs = FileSystemStorage()

            # Getting the paths
            file_video_path = os.path.join(fs.location, video.file_video.name)
            thumbnail_path = os.path.join(fs.location, video.thumbnail.name)

            # Deleting the files using with open
            with open(file_video_path, 'rb'):
                pass  # Open the file to make sure it's closed
            with open(thumbnail_path, 'rb'):
                pass  # Open the file to make sure it's closed

            # Deleting the database record
            video.delete()

            # Optionally, you can delete the entire directory if needed
            directory_path = os.path.join(fs.location, 'your_directory_name')
            os.rmdir(directory_path)

            messages.success(request, 'Konten Berhasil Dihapus!')
        except Exception as e:
            messages.error(request, f'Error deleting content: {str(e)}')

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
#end of delete_video

#start of like_video
def like_video(request):
    referring_url = request.META.get('HTTP_REFERER')
    username = request.user.username
    video_id = request.GET.get('video_id')

    post = PostVideo.objects.get(id=video_id)

    like_filter = LikePost.objects.filter(video_id=video_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(video_id=video_id, username=username)
        new_like.save()
        post.no_of_like += 1
        post.save()
        return redirect(referring_url)
    else:
        like_filter.delete()
        post.no_of_like -= 1
        post.save()
        return redirect(referring_url)
#end of like_video

#start of view_video
def view_video(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    videos = PostVideo.objects.all()

    video_df = pd.DataFrame.from_records(videos.values())
    if PostVideo.objects.all().exists():
        sort_option = request.GET.get('sort', 'latest')  # Default to sorting by latest
        if sort_option == 'latest':
            video_df = video_df.sort_values(by='created_at', ascending=False)
        elif sort_option == 'most_liked':
            video_df = video_df.sort_values(by='no_of_like', ascending=False)
    
        sorted_post_ids = video_df['id'].tolist()
        video = sorted(videos, key=lambda x: sorted_post_ids.index(x.id))

        return render(request, 'konten/video.html', {'video': video, 'profile': profile})
    else:
        return render(request, 'konten/video.html', {'profile': profile})
#end of view_video

#start of download_video
def download_video(request, video_id):
    video = get_object_or_404(PostVideo, id=video_id)
    file_path = video.file_video.path

    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type=mimetypes.guess_type(file_path)[0])
        response['Content-Disposition'] = f'attachment; filename="{video.file_video.name}"'
        return response
#end of download_video

#END CRUD VIDEO

#CRUD Modul Dokumen
#start of upload_modul
def upload_modul(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        file_modul = request.FILES.get('file_modul')
        thumbnail = request.FILES.get('thumbnail')
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        allowed_formats = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

        if file_modul and file_modul.content_type not in allowed_formats:
            messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .pdf: {file_modul.name}', extra_tags='form_upload_modul')
        else:
            new_post = PostModul.objects.create(
                user=user,
                judul=judul,
                deskripsi=deskripsi,
                kategori_id=kategori_instance,
                lisensi_id=lisensi_instance,
                thumbnail=thumbnail,
                file_modul=file_modul,
            )
            messages.success(request, 'Konten Berhasil Diupload', extra_tags='form_upload_modul')
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, 'upload/upload_modul.html', {'kategori': kategori, 'lisensi': lisensi, 'profile': profile})
#end of upload_modul

#start of update_modul
def update_modul(request, modul_id):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    kategori = Kategori.objects.all()
    lisensi = Lisensi.objects.all()
    modul = PostModul.objects.get(id=modul_id)

    if request.method == 'POST':
        user = request.user
        judul = request.POST['judul']
        deskripsi = request.POST['deskripsi']
        kategori_id = request.POST['kategori']
        lisensi_id = request.POST['lisensi']
        file_modul = request.FILES.get('file_modul')

        if request.FILES.get('thumbnail') == None:
            modul.thumbnail = modul.thumbnail
        elif request.FILES.get('thumbnail') != None:
            modul.thumbnail = request.FILES['thumbnail']

        kategori_instance = Kategori.objects.get(id=kategori_id)
        lisensi_instance = Lisensi.objects.get(id=lisensi_id)

        modul.judul = judul
        modul.deskripsi = deskripsi
        modul.kategori_id = kategori_instance
        modul.lisensi_id = lisensi_instance
        modul.save()

        if file_modul:
            allowed_formats = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if file_modul.content_type not in allowed_formats:
                messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .pdf: {file_modul.name}', extra_tags='form_update_modul')
            else:
                modul.file_modul = file_modul
                modul.save()
        messages.success(request, 'Konten Berhasil Diupdate', extra_tags='form_update_modul')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'update/update_modul.html', {'modul': modul, 'kategori': kategori, 'lisensi': lisensi, 'profile': profile})
#end of update_modul

#start of like_modul
def like_modul(request):
    referring_url = request.META.get('HTTP_REFERER')
    username = request.user.username
    modul_id = request.GET.get('modul_id')

    post = PostModul.objects.get(id=modul_id)

    like_filter = LikePost.objects.filter(modul_id=modul_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(modul_id=modul_id, username=username)
        new_like.save()
        post.no_of_like += 1
        post.save()
        return redirect(referring_url)
    else:
        like_filter.delete()
        post.no_of_like -= 1
        post.save()
        return redirect(referring_url)

def delete_modul(request, modul_id):
    modul = PostModul.objects.get(id=modul_id)

    if request.method == 'POST':
        if modul.file_modul:
            # Adjust the folder structure based on your media root and upload_to settings
            os.remove(modul.file_modul.path)
        if modul.thumbnail:
            os.remove(modul.thumbnail.path)
        modul.delete()

        messages.success(request, 'Konten Berhasil Dihapus!')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])  # Redirect to the home page after deletion
    else:
        # Handle GET request, render confirmation page
        return render(request, 'profile', {'modul': modul})
#end of like_modul

#start of view_modul
def view_modul(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    moduls = PostModul.objects.all()
    modul_df = pd.DataFrame.from_records(moduls.values())

    if PostModul.objects.all().exists():
        sort_option = request.GET.get('sort', 'latest')  # Default to sorting by latest
        if sort_option == 'latest':
            modul_df = modul_df.sort_values(by='created_at', ascending=False)
        elif sort_option == 'most_liked':
            modul_df = modul_df.sort_values(by='no_of_like', ascending=False)
        
        sorted_post_ids = modul_df['id'].tolist()
        modul = sorted(moduls, key=lambda x: sorted_post_ids.index(x.id))

        return render(request, 'konten/modul.html', {'modul': modul, 'profile': profile})
    else:
        return render(request, 'konten/modul.html', {'profile': profile})
#END CRUD Modul Dokeumen

#searching konten
def linear_search_konten(query, model):
    results = []
    for field in ['judul']:
        results.extend(model.objects.filter(**{f'{field}__icontains': query}))
    return results

def search_konten(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    
    if request.method == 'POST':
        search_query = request.POST['search']
        
        post = linear_search_konten(search_query, Post)
        video = linear_search_konten(search_query, PostVideo)
        modul = linear_search_konten(search_query, PostModul)
        
        post_images = PostImage.objects.filter(post__in=post)
        lisensi = Lisensi.objects.all()
        
        return render(request, 'search.html', {
            'post': post,
            'images': post_images,
            'lisensi': lisensi,
            'video': video,
            'modul': modul,
            'profile': profile,
        })
    
#end search
    
