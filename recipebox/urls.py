from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from recipes import views

admin.site.site_header = "Recipe Box admin"
admin.site.site_title = "Recipe Box"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("healthz", views.healthz, name="healthz"),
    path("api/recipes", views.recipes_collection, name="recipes"),
    path("api/recipes/<int:pk>", views.recipe_detail, name="recipe"),
    path("api/recipes/<int:pk>/photos", views.recipe_photos, name="recipe_photos"),
    path("api/photos/<int:pk>", views.photo_delete, name="photo_delete"),
    path("api/read", views.read_recipe, name="read_recipe"),
    path("photos/<int:pk>", views.photo_file, name="photo"),
    path("admin/", admin.site.urls),
]
