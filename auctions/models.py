from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    category = models.CharField(max_length=32)
    photo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    starting_bid = models.DecimalField(decimal_places=2, max_digits=10)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="listings")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} | {self.title} | {self.category}"


class Bid(models.Model):
    time_stamp = models.DateTimeField(auto_now=True)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bids")
    bid_amount = models.DecimalField(decimal_places=2, max_digits=7)

    def __str__(self):
        return f"{self.user} | ${self.bid_amount} | listing {self.listing_id}"


class Comment(models.Model):
    time_stamp = models.DateTimeField(auto_now=True)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=1024)

    def __str__(self):
        return f"{self.user} | '{self.comment}' | listing {self.listing_id}"


class Watchlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="watchlist")
    listings = models.ManyToManyField(Listing)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}"
