from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django import forms
import math
from decimal import Decimal

from .models import *




### FORMS ###

class CreateListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64)
    description = forms.CharField(label="Description (max. 1024 characters)", widget=forms.Textarea(attrs={'cols':10, 'rows':8}), max_length=1024)
    category = forms.CharField(label="Category", max_length=32)
    photo_url = forms.URLField(label="Photo URL (optional)", required=False)
    starting_bid = forms.DecimalField(label="Starting bid (USD)", decimal_places=2, max_digits=7, max_value=9999.99, widget=forms.TextInput(attrs={'id': 'bid-field'}))
    
class EditListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64)
    description = forms.CharField(label="Description (max. 1024 characters)", widget=forms.Textarea(attrs={'cols':10, 'rows':8}), max_length=1024)
    category = forms.CharField(label="Category", max_length=32)
    photo_url = forms.URLField(label="Photo URL (optional)", required=False)

class CommentForm(forms.Form):
    comment = forms.CharField(label="Leave comment", widget=forms.Textarea(attrs={'cols':10, 'rows':3}), max_length=1024)




### FUNCTIONS ###

# adds highest bid, bidder and the bid count to a listings object
def add_bidinfo(listings):
    for listing in listings:
        if Bid.objects.filter(listing = listing.id):
            listing.bid_count = Bid.objects.filter(listing = listing.id).count()
            listing.highest_bid = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].bid_amount
            listing.highest_bidder = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].user
        else:
            listing.bid_count = None
            listing.highest_bid = None
            listing.highest_bidder = None
    
    return listings
    
    


### MAIN PAGES ###

def index(request):
    
    # get list of active listings
    listings = Listing.objects.filter(is_active = True)
    add_bidinfo(listings)
    
    return render(request, "auctions/index.html", {
        "listings": listings,
        "title": "Active Listings",
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
        form = EditListingForm(request.POST)
        if form.is_valid():
            listing.title = form.cleaned_data["title"]
            listing.description = form.cleaned_data["description"]
            listing.category = form.cleaned_data["category"].casefold()
            listing.photo_url = form.cleaned_data["photo_url"]
            listing.save()
        return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
    

    # create form pre-populated with listing's data
    form = EditListingForm({
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "photo_url": listing.photo_url,
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
        current_highest_bid = None
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
    try:
        watchlist, created = Watchlist.objects.get_or_create(user=request.user)
        if listing in watchlist.listings.all():
            is_watchlist = True
        else:
            is_watchlist = False
    except TypeError:
        is_watchlist = False
        
    # get comments
    try:
        comments = Comment.objects.filter(listing = listing_id).all()
    except ObjectDoesNotExist:
        comments = None
        
    # add comment form
    comment_form = CommentForm()
    
    # calculate minimum bid for form validation min value
    if current_highest_bid:
        min_bid = round(current_highest_bid + Decimal(0.01), 2)
    else: 
        min_bid = round(listing.starting_bid + Decimal(0.01), 2)
    
    # create form within this view to is has access to this views variables for easier client-side validation
    class BidForm(forms.Form):
        bid_amount = forms.DecimalField(label="Bid amount", decimal_places=2, max_digits=7, min_value = min_bid, max_value=10000, widget=forms.NumberInput(attrs={'placeholder': f"{min_bid:.2f} or more", 'id': 'bid-field'}))
    
    bid_form = BidForm()
    bid_error = None
    this_bid = None
    
    
    # POST 
    if request.method == "POST":
        print(request.POST)
        
        # button actions for delete, edit, end, watchlist
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
            bid_form = BidForm(request.POST)
            
            if bid_form.is_valid():
                this_bid = bid_form.cleaned_data["bid_amount"]
                bid = Bid(
                    user_id = request.user.id,
                    listing_id = listing_id,
                    bid_amount = this_bid
                    )
                bid.save()
                return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
            else:
                this_bid = None
                # create the form already instantiated with the submitted bid data
                bid_form = BidForm(initial={"bid_amount": request.POST["bid_amount"]})
                bid_error = "Please enter a valid bid"

        # comment section
        if "comment" in request.POST:
            comment_form = CommentForm(request.POST)
            
            if comment_form.is_valid():
                comment = Comment(
                    comment = comment_form.cleaned_data["comment"],
                    listing = listing,
                    user = request.user
                    )
                comment.save()
                return HttpResponseRedirect(reverse("listing", kwargs={"listing_id": listing_id}))
                
    # return the listings page
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": bid_form,
        "bid_error": bid_error,
        "this_bid": this_bid,
        "current_highest_bid": current_highest_bid,
        "current_highest_bidder": current_highest_bidder,
        "is_watchlist": is_watchlist,
        "comments": comments,
        "comment_form": comment_form,
    })



def categories(request):
    
    listings = Listing.objects.filter(is_active = True).order_by("category")
    
    categories = []
    
    for listing in listings:
        if listing.category not in categories:
            categories.append(listing.category)
        
    return render(request, "auctions/categories.html", {
        "categories": categories,
    })



def category(request, category_name):
    
    listings = Listing.objects.filter(is_active = True).filter(category = category_name)
    add_bidinfo(listings)
        
    return render(request, "auctions/index.html", {
        "listings": listings,
        "title": f"Category: {category_name.title()}",
    })



def watchlist(request):
    
    try:
        watchlist = Watchlist.objects.get(user = request.user)
        watchlist_items = watchlist.listings.order_by("-is_active").all()
    except ObjectDoesNotExist:
        watchlist_items = None
    
    add_bidinfo(watchlist_items)
    
    
    # remove listing from watchlist
    if request.method == "POST":
        if "remove_from_watchlist" in request.POST:
            print(request.POST["listing_id"])
            listing = Listing.objects.get(id=request.POST["listing_id"])
            watchlist.listings.remove(listing)
            watchlist.save()
            watchlist_items = watchlist.listings.all()
        
    return render(request, "auctions/index.html", {
        "listings": watchlist_items,
        "title": "My Watchlist",
    })



def mylistings(request):
    
    # get list of active listings
    listings = Listing.objects.filter(user = request.user).order_by("-is_active")
    
    # get highest bid for each listing from Bid table
    for listing in listings:
        if Bid.objects.filter(listing = listing.id):
            listing.bid_count = Bid.objects.filter(listing = listing.id).count()
            listing.highest_bid = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].bid_amount
            listing.highest_bidder = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].user
        else:
            listing.highest_bid = None
    
    return render(request, "auctions/index.html", {
        "listings": listings,
        "title": "My Listings",
    })



def mybids(request):
    
    # get list of active listings which the current user has bid on
    listings = Listing.objects.filter(bids__user = request.user).order_by("-is_active")
    bid_listings = []
    
    for listing in listings:
        if listing not in bid_listings:
            bid_listings.append(listing)
    print(bid_listings)
    
    # get highest bid and bidder for each listing from Bid table
    for listing in listings:
        if Bid.objects.filter(listing = listing.id):
            listing.bid_count = Bid.objects.filter(listing = listing.id).count()
            listing.highest_bid = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].bid_amount
            listing.highest_bidder = Bid.objects.filter(listing = listing.id).order_by('-bid_amount')[0].user
        else:
            listing.highest_bid = None
    
    return render(request, "auctions/index.html", {
        "listings": bid_listings,
        "title": "My Bids",
    })




### USER MANAGEMENT (Pre-made by CS50W staff) ###

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
