from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django import forms

from .models import *


### forms ###

class CreateListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'cols':10, 'rows':3}), max_length=1024)
    category = forms.CharField(label="Category", max_length=32)
    photo_url = forms.URLField(label="Photo URL (optional)", required=False)
    starting_bid = forms.DecimalField(label="Starting bid (USD)", decimal_places=2, max_digits=7, max_value=9999.99)
    
    
    

### main pages ###

def index(request):
    
    # get list of active listings
    listings = Listing.objects.filter(is_active = True)
    
    # get highest bid for each listing from Bid table
    for listing in listings:
        if Bid.objects.filter(listing = listing.id):
            listing.bid_count = Bid.objects.filter(listing = listing.id).count()
            listing.highest_bid = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].bid_amount
        else:
            listing.highest_bid = None
    
    return render(request, "auctions/index.html", {
        "listings": listings,
    })



@login_required()
def create(request):
    
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            listing = Listing(
                title = form.cleaned_data["title"],
                description = form.cleaned_data["description"],
                category = form.cleaned_data["category"].casefold(),
                photo_url = form.cleaned_data["photo_url"],
                starting_bid = form.cleaned_data["starting_bid"],
                user = request.user
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
    try:
        listing = Listing.objects.get(id=listing_id)
    except ObjectDoesNotExist:
        return render(request, "auctions/edit.html", {
            "error_message": "No listing found"
        })
    
    
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            listing.title = form.cleaned_data["title"]
            listing.description = form.cleaned_data["description"]
            listing.category = form.cleaned_data["category"].casefold()
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
        "form": form,
    })



def listing(request, listing_id):
    
    # check if bids exist for this listing and set bid-related variables
    if Bid.objects.filter(listing = listing_id):
        current_highest_bid = Bid.objects.filter(listing = listing_id).order_by('-bid_amount')[0].bid_amount
        current_highest_bidder = Bid.objects.filter(listing = listing_id).order_by('-bid_amount')[0].user
    else:
        current_highest_bid = 0.00
        current_highest_bidder = None
    
    # get listing content and return error message if listing does not exist
    try:
        listing = Listing.objects.get(id=listing_id)
    except ObjectDoesNotExist:
        return render(request, "auctions/listing.html", {
        "error_message": "No listing found"
    })
    
    # get watchlist status
    # get_or_create returns a tuple and so requires the 'created' part which returns True if created and False if not
    watchlist, created = Watchlist.objects.get_or_create(user=request.user)
    
    if listing in watchlist.listings.all():
        is_watchlist = True
    else:
        is_watchlist = False
    
    # create form within this view to is has access to this views variables for easier client-side validation
    class BidForm(forms.Form):
        bid_amount = forms.DecimalField(label="Bid amount (USD)", decimal_places=2, max_digits=7, min_value=max(current_highest_bid, listing.starting_bid) + 1)
    
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
            
        if "toggle-watchlist" in request.POST:
            # add or remove toggle from watchlist
            if listing in watchlist.listings.all():
                watchlist.listings.remove(listing)
                is_watchlist = False
            else:
                watchlist.listings.add(listing)
                is_watchlist = True
            watchlist.save()
            
        # bid section
        if "bid_amount" in request.POST:
            this_bid = float(request.POST["bid_amount"])
            print(this_bid)
            print(current_highest_bid)
            print(Listing.starting_bid)
            
            # server-side validation - return listing page with error message if submitted bid is too low
            if this_bid <= current_highest_bid or this_bid <= listing.starting_bid: 
                # create the form already instantiated with the submitted bit date
                bid_form = BidForm(initial={"bid_amount": this_bid})
                
                # 
                if current_highest_bid == 0.00:
                    current_highest_bid = None
                    
                return render(request, "auctions/listing.html", {
                    "listing_id": listing_id,
                    "bid_error": "This bid is too low",
                    "this_bid": this_bid,
                    "listing": listing,
                    "bid_form": bid_form,
                    "current_highest_bid": current_highest_bid,
                    "current_highest_bidder": current_highest_bidder
                })
            
            bid = Bid(
                user_id = request.user.id,
                listing_id = listing_id,
                bid_amount = this_bid
                )
            bid.save()
            return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
    
    if current_highest_bid == 0.00:
        current_highest_bid = None
    
    bid_form = BidForm()
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": bid_form,
        "current_highest_bid": current_highest_bid,
        "current_highest_bidder": current_highest_bidder,
        "is_watchlist": is_watchlist
    })


  
### Categories ###

def categories(request):
    
    listings = Listing.objects.filter(is_active = True).order_by("category")
    
    categories = []
    
    for listing in listings:
        if listing.category not in categories:
            categories.append(listing.category)
        
    return render(request, "auctions/categories.html", {
        "categories": categories,
    })

### Category ###

def category(request, category_name):
    
    listings = Listing.objects.filter(is_active = True).filter(category = category_name)
    
    # get highest bid for each listing from Bid table
    for listing in listings:
        if Bid.objects.filter(listing = listing.id):
            listing.bid_count = Bid.objects.filter(listing = listing.id).count()
            listing.highest_bid = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].bid_amount
        else:
            listing.highest_bid = None
        
    return render(request, "auctions/category.html", {
        "listings": listings,
        "category_name": category_name,
    })










### USER MANAGEMENT ###

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
