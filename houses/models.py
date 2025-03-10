from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
import requests
from django.conf import settings
from cloudinary.models import CloudinaryField
class House(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    contact = models.CharField(max_length=20)
    is_taken = models.BooleanField(default=False)
    video = CloudinaryField('house_video', resource_type='video', blank=True, null=True)
    rent = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class HouseImage(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="house_images")  
    image = CloudinaryField('image',default='None')

    def __str__(self):
        return f"Image for {self.house.name}"


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")  # ✅ Track payment status
    paid_on = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField(null=True, blank=True)  # ✅ Set after payment success

    def save(self, *args, **kwargs):
        """Set expiration date only if the payment is successful."""
        if self.status == "success" and not self.expires_on:
            self.expires_on = now() + timedelta(days=14)  # ✅ Give 14 days access
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expires_on and now() > self.expires_on

    def __str__(self):
        return f"{self.user.username} - {self.location} ({'Expired' if self.is_expired() else self.status})"

    def verify_payment(self):
        """Verify payment status using Paystack API."""
        url = f"https://api.paystack.co/transaction/verify/{self.reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("status") and data["data"]["status"] == "success":
            self.status = "success"
            self.expires_on = now() + timedelta(days=1)  # ✅ Update expiration only if successful
            self.save()
            return True
        else:
            self.status = "failed"
            self.save()
            return False

    def __str__(self):
        return f"{self.user.username} - {self.location} ({'Expired' if self.is_expired() else 'Active'})"
