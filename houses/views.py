from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now, timedelta
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
import requests
import uuid
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import House, HouseImage, Payment
from .forms import HouseForm, HouseImageForm
from django.urls import reverse

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


### ✅ HOUSE LIST VIEW WITH SEARCH, FILTER, PAGINATION
def house_list(request):
    query = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()

    houses = House.objects.filter(is_taken=False)

    # Search Filter
    if query:
        houses = houses.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )

    # Location Filter
    if location_filter and location_filter.lower() != "all":
        houses = houses.filter(location__iexact=location_filter)

    # Unique Locations for Dropdown
    locations = House.objects.values_list('location', flat=True).distinct()

    # PAGINATION (6 Houses per Page)
    paginator = Paginator(houses, 6)
    page_number = request.GET.get('page')
    houses_page = paginator.get_page(page_number)

    return render(request, "houses/house_list.html", {
        "houses": houses_page,
        "query": query,
        "location_filter": location_filter,
        "locations": locations,
    })


def view_house(request, house_id):
    house = get_object_or_404(House, id=house_id)
    images = HouseImage.objects.filter(house=house)  # Fetch all images related to this house

    return render(request, "houses/view_house.html", {"house": house, "images": images})


### ✅ HOUSE DETAIL VIEW
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import House, Payment
from urllib.parse import unquote

@login_required
def house_detail(request, house_id):
    house = get_object_or_404(House, id=house_id)
    user = request.user
    location = house.location

    existing_payment = Payment.objects.filter(
        user=user,
        location=location,
        status="Success",
        expires_on__gte=now()
    ).first()

    if not existing_payment:
        messages.info(request, "Please complete payment to access this house.")

    # Proceed to render the house detail page
    return render(request, 'houses/house_detail.html', {'house': house})

@login_required
def add_house(request):
    if request.method == "POST":
        house_form = HouseForm(request.POST, request.FILES)
        if house_form.is_valid():
            house = house_form.save()
            return redirect('house_detail', house_id=house.id)  # Fixed redirect
    else:
        house_form = HouseForm()

    return render(request, 'houses/add_house.html', {'house_form': house_form})


### ✅ ADD HOUSE IMAGES
@login_required
def add_house_images(request, house_id):
    house = get_object_or_404(House, id=house_id)

    if request.method == 'POST':
        image_form = HouseImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            image = image_form.save(commit=False)
            image.house = house
            image.save()
            return redirect('house_detail', house_id=house.id)  # Fixed redirect
    else:
        image_form = HouseImageForm()

    return render(request, 'houses/add_house_images.html', {
        'image_form': image_form, 'house': house
    })


### ✅ INITIATE PAYSTACK PAYME
@login_required
def initiate_payment(request, location, house_id=None):
    user = request.user
    location = unquote(location)  # ✅ Decode URL-encoded location
    amount = 500  # Set your price here
    reference = str(uuid.uuid4())

    # Prevent double payment
    existing_payment = Payment.objects.filter(
        user=user,
        location=location,
        status="success",
        expires_on__gte=now()
    ).first()

    if existing_payment:
        messages.success(request, f"You already have access to {location} until {existing_payment.expires_on}.")
        if house_id:
            return redirect("house_detail", house_id=house_id)
        return redirect("house_list")

    # Build callback URL dynamically
    if house_id:
        callback_url = request.build_absolute_uri(
            reverse("verify_payment_with_house", args=[reference, house_id])
        )
    else:
        callback_url = request.build_absolute_uri(
            reverse("verify_payment", args=[reference])
        )

    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": f"{user.username}@gmail.com",
        "amount": int(amount * 100),
        "reference": reference,
        "callback_url": callback_url
    }

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
        response_data = response.json()

        if response_data.get("status"):
            Payment.objects.create(
                user=user,
                location=location,
                amount=amount,
                reference=reference,
                status="pending",
                expires_on=None
            )
            return redirect(response_data["data"]["authorization_url"])

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Payment could not be initialized. Error: {e}")

    return redirect("house_list")


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY

@login_required
def verify_payment(request, reference, house_id=None):
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    payment = None  # Initialize payment early for later use

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            payment = Payment.objects.filter(reference=reference, user=request.user).first()

            if payment:
                payment.status = "success"
                payment.expires_on = now() + timedelta(days=3)  # or 7 days if you prefer
                payment.save()
                messages.success(request, f"✅ Payment successful! You now have access to {payment.location}.")

                if house_id:
                    return redirect("house_detail", house_id=house_id)
                return redirect("house_list")

        messages.error(request, "❌ Payment verification failed.")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"⚠️ Error verifying payment: {e}")

    # Redirect back to initiate payment if payment exists, otherwise to house list
    if payment:
        return redirect("initiate_payment", location=payment.location, house_id=house_id if house_id else None)
    return redirect("house_list")


from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


from .forms import CustomUserCreationForm  # ✅ use your custom form

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful! Welcome.")
            return redirect("house_list")
    else:
        form = CustomUserCreationForm()

    return render(request, "houses/signup.html", {"form": form})
def view_location(request, location):
    # Check if user has a valid payment for this location
    user_has_paid = Payment.objects.filter(
        user=request.user, 
        location=location, 
        expires_on__gte=now()
    ).exists()

    if not user_has_paid:
        return redirect("initiate_payment", location=location)  # Redirect to payment page if not paid

    # Get all houses in this location
    houses = House.objects.filter(location=location)
    
    return render(request, "houses/location_houses.html", {"houses": houses, "location": location})

from django.contrib import messages

from .forms import HouseForm

@login_required
def post_house(request):
    if not request.user.can_post:
        return redirect("home")

    if request.method == "POST":
        form = HouseForm(request.POST)
        
        if form.is_valid():
            house = form.save(commit=False)
            house.owner = request.user
            house.is_taken = request.POST.get("is_taken") == "on"  # Allow users to set "is_taken"
            house.save()

            # ✅ Handle Cloudinary image URLs
            image_urls = request.POST.get("image_urls", "").split(",")
            for url in image_urls:
                if url.strip():
                    HouseImage.objects.create(house=house, image=url)  # Save Cloudinary URL

            return redirect("house_list")

    else:
        form = HouseForm()
    
    return render(request, "houses/post_house.html", {"form": form})
@login_required
def my_houses(request):
    """ Shows houses posted by the logged-in user (only if they can post) """
    if not request.user.can_post:
        messages.error(request, "You are not allowed to post houses.")
        return redirect("house_list")

    houses = House.objects.filter(owner=request.user)
    return render(request, "houses/my_houses.html", {"houses": houses})

@login_required
def edit_house(request, house_id):
    house = get_object_or_404(House, id=house_id, owner=request.user)

    if not request.user.can_post:
        messages.error(request, "You are not allowed to edit houses.")
        return redirect("house_list")

    if request.method == "POST":
        form = HouseForm(request.POST, request.FILES, instance=house)
        if form.is_valid():
            house = form.save(commit=False)
            house.is_taken = 'is_taken' in request.POST  # Ensure checkbox updates correctly
            house.save()
            messages.success(request, "House updated successfully!")
            return redirect("my_houses")
    else:
        form = HouseForm(instance=house)

    return render(request, "houses/post_house.html", {"form": form, "house": house})

