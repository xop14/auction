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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ID: {self.id}, \nTitle: {self.title}, \nCategory: {self.category}, \nDescription: {self.description}, \nPhoto URL: {self.photo_url}, \nActive: {self.is_active}, \nStarting Bid: {self.starting_bid}, \nCreated: {self.created}, \nUpdated: {self.updated}"

class Bid(models.Model): 
    time_stamp = models.DateTimeField(auto_now=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    bid_amount = models.DecimalField(decimal_places=2, max_digits=7)
    
    def __str__(self):
        return f"""
                TimeStamp: {self.time_stamp}
                Listing ID: {self.listing_id}
                User ID: {self.user}
                Bid Amount: {self.bid_amount}
                """

class Comment(models.Model):
    time_stamp = models.DateTimeField(auto_now=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=1024)
    
    def __str__(self):
        return f"""
                TimeStamp: {self.time_stamp}
                Listing ID: {self.listing_id}
                User ID: {self.user}
                Comment: {self.comment}
                """
