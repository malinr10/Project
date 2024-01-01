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

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return render(request, 'index.html')


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
                messages.info(request, 'Username already taken')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken')
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
            messages.info(request, 'Password not matching')
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
            messages.info(request, 'Invalid Credentials')
            return redirect('login')
    else:
        return render(request, 'login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')
#End of User Authentication

#Start of User Interface
#Start of Home Page
@login_required(login_url='login')
def homePage(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    post = Post.objects.all()
    video = PostVideo.objects.all()
    modul = PostModul.objects.all()
    images = PostImage.objects.filter(post__in=post)
    lisensi = Lisensi.objects.all()

    all_posts = sorted(
        list(post) + list(video) + list(modul),
        key=lambda post: post.created_at,
        reverse=True
    )

    latest_posts = all_posts[:5]

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

def detail(request, id):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    post = Post.objects.get(id_post=id)
    photos = PostImage.objects.filter(post=post)
    return render(request, 'detail/detail.html', {'post': post, 'photos': photos, 'profile': profile})

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

#Start of CRUD Image
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
            messages.error(request, f'Format File Tidak Sesuai!!!, Gunakan Format .jpg, .jpeg, dan .png: {thumbnail.name}')

        new_post = Post.objects.create(user=user, judul=judul, deskripsi=deskripsi, kategori_id=kategori_instance, lisensi_id=lisensi_instance, thumbnail=thumbnail) 

        for image in images:
            if image.content_type not in allowed_formats:
                messages.error(request, f'Format File Tidak Sesuai!!!, Gunakan Format .jpg, .jpeg, dan .png: {image.name}')
            else:
                PostImage.objects.create(post=new_post, image=image)

        messages.success(request, 'Konten Berhasil Diupload')

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
    
def view_image(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    post = Post.objects.all()

    sort_option = request.GET.get('sort', 'latest')  # Default to sorting by latest
    if sort_option == 'latest':
        post = Post.objects.all().order_by('-created_at')  
    elif sort_option == 'most_liked':
        post = Post.objects.all().order_by('-no_of_like')
    return render(request, 'konten/gambar.html', {'post': post, 'profile': profile})

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
        
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        user = request.user
        user_model = User.objects.get(username=user)
        profile = Profile.objects.get(user=user_model)
        context = {
            'profile': profile,
        }
        return render(request, 'setting.html', context)

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
            messages.error(request, 'Password lama tidak benar.')
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        # Verifikasi konfirmasi password baru
        if new_password != confirm_new_password:
            messages.error(request, 'Konfirmasi password baru tidak cocok.')
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        # Set password baru dan perbarui session auth hash
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('settings')

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
    

#CRUD VIDEO

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
            messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .mp4, .avi, dan .mkv: {file_video.name}')
        elif not file_video and not link_video:
            messages.error(request, 'Harap unggah file video atau masukkan tautan YouTube.')
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
                    messages.success(request, 'Konten Berhasil Diupload')
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])
                else:
                    messages.error(request, 'Tautan YouTube tidak valid.')
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
                messages.success(request, 'Konten Berhasil Diupload')
                return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, 'upload/upload_video.html', {'kategori': kategori, 'lisensi': lisensi, 'profile': profile})

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
            allowed_formats = ['video/mp4', 'video/avi', 'video/mkv']
            if file_video.content_type not in allowed_formats:
                messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .mp4, .avi, dan .mkv: {file_video.name}')
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
                messages.error(request, 'Tautan YouTube tidak valid.')

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'update/update_video.html', {'video': video, 'kategori': kategori, 'lisensi': lisensi, 'profile': profile})

def delete_video(request, video_id):
    video = PostVideo.objects.get(id=video_id)

    if request.method == 'POST':
        try:
            fs = FileSystemStorage()

            if video.file_video:
                fs.delete(video.file_video.name)

            if video.thumbnail:
                fs.delete(video.thumbnail.name)

            video.delete()
            messages.success(request, 'Konten Berhasil Dihapus!')
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        except Exception as e:
            messages.error(request, f'Error deleting content: {str(e)}')

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


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
    
def view_video(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    video = PostVideo.objects.all()

    sort_option = request.GET.get('sort', 'latest')  # Default to sorting by latest
    if sort_option == 'latest':
       
        video = PostVideo.objects.all().order_by('-created_at')
    elif sort_option == 'most_liked':

        video = PostVideo.objects.all().order_by('-no_of_like')
    return render(request, 'konten/video.html', {'video': video, 'profile': profile})

def download_video(request, video_id):
    video = get_object_or_404(PostVideo, id=video_id)
    file_path = video.file_video.path

    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type=mimetypes.guess_type(file_path)[0])
        response['Content-Disposition'] = f'attachment; filename="{video.file_video.name}"'
        return response
    
#END CRUD VIDEO

#CRUD Modul Dokumen
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
            messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .pdf: {file_modul.name}')
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
            messages.success(request, 'Konten Berhasil Diupload')
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, 'upload/upload_modul.html', {'kategori': kategori, 'lisensi': lisensi, 'profile': profile})

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
                messages.error(request, f'Format File Tidak Sesuai!!! Gunakan Format .pdf: {file_modul.name}')
            else:
                modul.file_modul = file_modul
                modul.save()

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request, 'update/update_modul.html', {'modul': modul, 'kategori': kategori, 'lisensi': lisensi, 'profile': profile})

def like_modul(request):
    referring_url = request.META.get('HTTP_REFERER')
    username = request.user.username
    modul_id = request.GET.get('modul_id')

    post = PostVideo.objects.get(id=modul_id)

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

def view_modul(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    modul = PostModul.objects.all()
    sort_option = request.GET.get('sort', 'latest')
    if sort_option == 'latest':
        modul = PostModul.objects.all().order_by('-created_at')
    elif sort_option == 'most_liked':
        modul = PostModul.objects.all().order_by('-no_of_like')
    return render(request, 'konten/modul.html', {'modul': modul, 'profile': profile})
#END CRUD Modul Dokeumen

#searching konten
def search_konten(request):
    user_object = User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user_object)
    if request.method == 'POST':
        search = request.POST['search']
        post = Post.objects.filter(judul__icontains=search)
        video = PostVideo.objects.filter(judul__icontains=search)
        modul = PostModul.objects.filter(judul__icontains=search)
        images = PostImage.objects.filter(post__in=post)
        lisensi = Lisensi.objects.all()
        return render(request, 'search.html', {'post': post, 'images': images, 'lisensi': lisensi, 'video': video, 'modul': modul, 'profile': profile})
#end search