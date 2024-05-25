from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render , get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User , Post , Follow , Like


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        return JsonResponse({"message": "Changes successful", "data": data["content"]})

def remove_like(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
        user = request.user
        like = Like.objects.filter(user=user, post=post).first()
        if like:
            like.delete()
            return JsonResponse({"message": "remove like successful"})
        else:
            return JsonResponse({"message": "like not found"}, status=404)
    except Post.DoesNotExist:
        return JsonResponse({"message": "Post not found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)
   

def add_like (request , post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newLike = Like(user=user, post=post)
    newLike.save()
    return JsonResponse({"message": "Like added" })

def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    paginator = Paginator(allPosts,5)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    allLikes = Like.objects.all()

    whoYouLiked = []

    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                whoYouLiked.append(like.post.id)
    except:
        whoYouLiked = []

    return render(request, "network/index.html",{
        "allPosts":allPosts,
        "posts_of_the_page":posts_of_the_page,
        "whoYouLiked":whoYouLiked
    })

def profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    all_posts = Post.objects.filter(user=user).order_by('-id')

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    is_following = False
    if request.user.is_authenticated:
        is_following = followers.filter(user=request.user).exists()

    paginator = Paginator(all_posts, 1)  # Paginate with 1 post per page
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        "allPosts": all_posts,
        "posts_of_the_page": posts_of_the_page,
        "username": user.username,
        "following": following,
        "followers": followers,
        "is_following": is_following,  # Updated to match template logic
        "user_profile": user
    })
def following(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))  # Redirect to login if not authenticated

    current_user = request.user
    following_people = Follow.objects.filter(user=current_user).values_list('user_follower', flat=True)
    following_posts = Post.objects.filter(user__in=following_people).order_by('-id')

    paginator = Paginator(following_posts, 5)  # Paginate with 5 posts per page
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "posts_of_the_page": posts_of_the_page
    })

    

def follow(request):
    if request.method == 'POST':
        userfollow_username = request.POST.get('userfollow')
        if userfollow_username:
            current_user = request.user
            user_to_follow = User.objects.get(username=userfollow_username)

            # Check if the follow relationship already exists
            follow_object, created = Follow.objects.get_or_create(user=current_user, user_follower=user_to_follow)

            if created:
                # Follow relationship was created, you are now following the user
                return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user_to_follow.id}))

    return HttpResponseRedirect(reverse('some_default_page'))


def unfollow(request):
    if request.method == 'POST':
        user_to_unfollow_username = request.POST.get('userfollow')
        if user_to_unfollow_username:
            current_user = request.user
            user_to_unfollow = User.objects.get(username=user_to_unfollow_username)

            # Check if the follow relationship exists
            follow_object = Follow.objects.filter(user=current_user, user_follower=user_to_unfollow).first()

            if follow_object:
                # Delete the follow relationship
                follow_object.delete()

            return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user_to_unfollow.id}))

    return HttpResponseRedirect(reverse('some_default_page'))
 


def newPost(request):
    if request.method == "POST":
        content = request.POST['content']
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content,user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")