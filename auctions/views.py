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


### forms ###

class CreateListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'cols':10, 'rows':3}), max_length=1024)
    category = forms.CharField(label="Category", max_length=32)
    photo_url = forms.URLField(label="Photo URL (optional)", required=False)
    starting_bid = forms.DecimalField(label="Starting bid (USD)", decimal_places=2, max_digits=7)
    
    
    

### main pages ###

def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all(),
        "current_user_id": request.user.id
    })



@login_required()
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



@login_required()
def edit(request, listing_id):
    
    # get listing content
    error_message = None
    
    try:
        listing = Listing.objects.get(id=listing_id)
    except ObjectDoesNotExist:
        error_message = "This listing does not exist"
        listing = None
    
    
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            listing.title = form.cleaned_data["title"]
            listing.description = form.cleaned_data["description"]
            listing.category = form.cleaned_data["category"]
            listing.photo_url = form.cleaned_data["photo_url"]
            listing.starting_bid = form.cleaned_data["starting_bid"]
            listing.save()
        return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
    

    form = CreateListingForm({
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "photo_url": listing.photo_url,
        "starting_bid": listing.starting_bid,
        })
    
    return render(request, "auctions/edit.html", {
        "listing_id": listing_id,
        "listing": listing,
        "error_message": error_message,
        "form": form,
    })



def listing(request, listing_id):
    
    error_message = None
    
    # check if bids exist for this listing and set bid-related variables
    if Bid.objects.filter(listing_id = listing_id):
        current_highest_bid = Bid.objects.filter(listing_id = listing_id).order_by('-bid_amount')[0].bid_amount
        bidder_id = Bid.objects.filter(listing_id = listing_id).order_by('-bid_amount')[0].user_id
        bidder_username = User.objects.get(id = bidder_id).username   
    else:
        current_highest_bid = 0.00
        bidder_id = None
        bidder_username = None
    
    # get listing content
    try:
        listing = Listing.objects.get(id=listing_id)
    except ObjectDoesNotExist:
        error_message = "This listing does not exist"
        listing = None
    
    
    # post
    if request.method == "POST":
        print(request.POST)
        
        # button actions for delete, edit, end
        if "delete" in request.POST:
            listing.delete()
            return HttpResponseRedirect(reverse("index"))
        if "edit" in request.POST:
            return HttpResponseRedirect(reverse("edit", kwargs={"listing_id": listing_id}))
        if "end" in request.POST:
            listing.is_active = False
            listing.save()
            
        # bid section
        if "bid_amount" in request.POST:
            this_bid = float(request.POST["bid_amount"])
            bid = Bid(
                user_id = request.user.id,
                listing_id = listing_id,
                bid_amount = this_bid
                )
            bid.save()
            return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
            
    
    # get listing creators username
    try:
        creator = User.objects.get(id=listing.user_id)
    except ObjectDoesNotExist:
        error_message = "This user no longer exists"
        creator = None
    
    # create form within this view to is has access to this views variables for easier validation
    class BidForm(forms.Form):
        bid_amount = forms.DecimalField(decimal_places=2, max_digits=7, min_value=max(current_highest_bid, listing.starting_bid) + 1)
    
    bid_form = BidForm()
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "error_message": error_message,
        "creator": creator,
        "bid_form": bid_form,
        "current_highest_bid": current_highest_bid,
        "bidder_username": bidder_username
    })







### user management ###

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