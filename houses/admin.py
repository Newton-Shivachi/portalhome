from django.contrib import admin
from .models import House, HouseImage, Payment

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
