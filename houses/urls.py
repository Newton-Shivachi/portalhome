from django.urls import path
from .views import house_list, house_detail,post_house, my_houses, edit_house, add_house, add_house_images,initiate_payment, verify_payment, view_location,view_house,logout_view, signup
from django.contrib.auth.views import LoginView
urlpatterns = [
    path('', house_list, name='house_list'),
    path('<int:house_id>/', house_detail, name='house_detail'),
    path("houses/<int:house_id>/", view_house, name="view_house"),
    path('add/', add_house, name='add_house'),
    path("login/", LoginView.as_view(template_name="houses/login.html"), name="login"),
    path('<int:house_id>/add_images/', add_house_images, name='add_house_images'),
    path("logout/", logout_view, name="logout"),
    path("payment/<str:location>/", initiate_payment, name="initiate_payment"),
    path("signup/", signup, name="signup"),
    path("payment/verify/<str:reference>/", verify_payment, name="verify_payment"),
    path("map/<str:location>/", view_location, name="view_location"),
    path("post-house/", post_house, name="post_house"),
    path("my-houses/", my_houses, name="my_houses"),
    path("edit-house/<int:house_id>/", edit_house, name="edit_house"),
]
