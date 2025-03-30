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
@login_required
def house_detail(request, house_id):
    house = get_object_or_404(House, id=house_id)
    houses_in_location = House.objects.filter(location=house.location).exclude(id=house.id)
    # Ensure user has a valid, verified payment
    user_has_paid = Payment.objects.filter(
        user=request.user, 
        location=house.location,
        status="success",  # ✅ Only successful payments
        expires_on__gte=now()  # ✅ Not expired
    ).exists()

    if not user_has_paid:
        return redirect("initiate_payment", location=house.location)  # Redirect to pay

    return render(request, "houses/house_detail.html", {"house": house, "user_has_paid": user_has_paid,"houses_in_location": houses_in_location})

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


### ✅ INITIATE PAYSTACK PAYMENT
@login_required
def initiate_payment(request, location):
    user = request.user
    amount = 150  # Amount in currency
    reference = str(uuid.uuid4())

    # Check if user already has a valid payment
    existing_payment = Payment.objects.filter(user=user, location=location, status="success").first()
    if existing_payment and not existing_payment.is_expired():
        messages.success(request, f"You already have access to {location} until {existing_payment.expires_on}.")
        return redirect("house_list")

    # Paystack Payment Initialization
    callback_url = request.build_absolute_uri(f'/payment/verify/{reference}/')
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": user.email,
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
                status="pending",  # ✅ Store as pending
                expires_on=None  # ✅ Set only after success
            )
            return redirect(response_data["data"]["authorization_url"])

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Payment could not be initialized. Error: {e}")
    
    return redirect("house_list")



### ✅ VERIFY PAYSTACK PAYMENT

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY

@login_required
def verify_payment(request):
    reference = request.GET.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    response_data = response.json()

    if response_data.get("status") and response_data["data"]["status"] == "success":
        # Fetch payment record
        payment = get_object_or_404(Payment, reference=reference)

        # Ensure the payment was actually successful before granting access
        payment.expires_on = now() + timedelta(days=14)  # Extend access time
        payment.save()

        messages.success(request, f"Payment successful! You can now view houses in {payment.location}.")
        return redirect("house_list")

    messages.error(request, "Payment verification failed.")
    return redirect("house_list")
def verify_payment(request, reference):
    """Verifies payment with Paystack and updates the database."""
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            payment = Payment.objects.filter(reference=reference, user=request.user).first()

            if payment:
                payment.status = "success"  # ✅ Mark as successful
                payment.expires_on = now() + timedelta(days=14)  # ✅ Set expiration
                payment.save()
                messages.success(request, f"Payment successful! You have access to {payment.location} until {payment.expires_on}.")
                return redirect("house_list")  # ✅ Redirect to house listings

        messages.error(request, "Payment verification failed. Please try again.")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error verifying payment: {e}")

    return redirect("initiate_payment", location=payment.location)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in the user
            messages.success(request, "Signup successful! Welcome.")
            return redirect("house_list")  # Redirect to home or another page
    else:
        form = UserCreationForm()

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
    """ Allows users to update their house details (only if they can post) """
    house = get_object_or_404(House, id=house_id, owner=request.user)

    if not request.user.can_post:
        messages.error(request, "You are not allowed to edit houses.")
        return redirect("house_list")

    if request.method == "POST":
        form = HouseForm(request.POST, request.FILES, instance=house)
        if form.is_valid():
            form.save()
            return redirect("my_houses")
    else:
        form = HouseForm(instance=house)

    return render(request, "houses/edit_house.html", {"form": form, "house": house})

