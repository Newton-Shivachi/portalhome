from django.contrib import admin
from .models import House, HouseImage, Payment, CustomUser
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "can_post", "is_staff", "is_active")
    list_editable = ("can_post",)  # Allow admins to toggle "can_post" in admin panel

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Payment)
class HouseImageInline(admin.TabularInline):  # Allows adding images inline
    model = HouseImage
    extra = 1  # Show one empty form for adding a new image
    
@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact', 'is_taken')  # Columns in list view
    list_filter = ('is_taken', 'location')  # Filters
    search_fields = ('name', 'location', 'contact')  # Search bar
    inlines = [HouseImageInline]  # Show images inside the house admin page

@admin.register(HouseImage)
class HouseImageAdmin(admin.ModelAdmin):
    list_display = ('house', 'image')  # Display image related to house
