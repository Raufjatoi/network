from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator

from .models import User , Post , Follow

def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    paginator = Paginator(allPosts,1)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    return render(request, "network/index.html",{
        "allPosts":allPosts,
        "posts_of_the_page":posts_of_the_page
    })

def profile(request , user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(user=user).order_by("id").reverse()

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    try:
        checkFollow = followers.filter(user=User.objects.get(pk=request.user.id ))

        if len (checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False



    except:
        isFollowing = False


    paginator = Paginator(allPosts,1)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    return render(request, "network/profile.html",{
        "allPosts":allPosts,
        "posts_of_the_page":posts_of_the_page,
        "username":user.username,
        "following": following,
        "followers":followers,
        "isfollowing":isFollowing,
        "user_profile":user
    })
def follow(request):
    if request.method == 'POST':
        userfollow_username = request.POST.get('userfollow')  # Ensure you're getting the username
        if userfollow_username:  # Check if the username is provided

            # Get the current user
            current_user = request.user

            # Get the user to follow
            user_to_follow = User.objects.get(username=userfollow_username)

            # Create a Follow object
            follow_object = Follow.objects.create(user=current_user, user_follower=user_to_follow)

            # Save the Follow object
            follow_object.save()

            # Redirect to the profile page of the user being followed
            return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user_to_follow.id}))

    # Handle invalid requests or GET requests by redirecting to some page
    return HttpResponseRedirect(reverse('some_default_page'))


def unfollow(request):
    if request.method == 'POST':
        user_to_unfollow_username = request.POST.get('userfollow')  # Ensure you're getting the username
        if user_to_unfollow_username:  # Check if the username is provided

            # Get the current user
            current_user = request.user

            # Get the user to unfollow
            user_to_unfollow = User.objects.get(username=user_to_unfollow_username)

            # Get the follow object if it exists
            follow_object = Follow.objects.filter(user=current_user, user_follower=user_to_unfollow).first()

            if follow_object:  # Check if the follow object exists
                # Delete the follow object
                follow_object.delete()

            # Redirect to the profile page of the user being unfollowed
            return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user_to_unfollow.id}))

    # Handle invalid requests or GET requests by redirecting to some page
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
