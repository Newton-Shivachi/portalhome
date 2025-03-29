from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
import requests
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    can_post = models.BooleanField(default=False)  # Only certain users can post houses

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    # Resolve related name conflicts
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups_set",  # ✅ Unique related_name
        blank=True,
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions_set",  # ✅ Unique related_name
        blank=True,
        help_text="Specific permissions for this user."
    )

class House(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Correct user reference
    posted_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=7)
    longitude = models.DecimalField(max_digits=9, decimal_places=7)
    contact = models.CharField(max_length=20)
    is_taken = models.BooleanField(default=False)
    video = CloudinaryField('house_video', resource_type='video', blank=True, null=True)
    rent = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.location} (by {self.owner.username})"

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
            self.expires_on = now() + timedelta(days=1)  # ✅ Give 1 days access
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
