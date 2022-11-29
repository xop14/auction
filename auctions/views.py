from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django import forms

from .models import User
from .models import Listing
from .models import Bid
from .models import Comment

class CreateListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'cols':10, 'rows':3}), max_length=1024)
    category = forms.CharField(label="Category", max_length=32)
    photo_url = forms.URLField(label="Photo URL (optional)", required=False)
    starting_bid = forms.DecimalField(label="Starting bid (USD)", decimal_places=2, max_digits=7)

def index(request):
    print(request.user.username)
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all(),
        "current_user_id": request.user.id,
    })
    
def create(request):
    
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            listing = Listing(
                title = form.cleaned_data["title"],
                description = form.cleaned_data["description"],
                category = form.cleaned_data["category"],
                photo_url = form.cleaned_data["photo_url"],
                starting_bid = form.cleaned_data["starting_bid"],
                user_id = request.user.id
            )
            listing.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/create.html", {
            "form": CreateListingForm(),
        })

def listing(request, listing_id):
    error_message = None
    
    try:
        listing = Listing.objects.get(id=listing_id)
    except ObjectDoesNotExist:
        error_message = "This listing does not exist"
        listing = None
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "error_message": error_message
    })

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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")