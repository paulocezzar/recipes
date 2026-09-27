from django.contrib import admin

from .models import Photo, Recipe


class PhotoInline(admin.TabularInline):
    model = Photo
    fields = ("position", "content_type", "created_at")
    readonly_fields = ("content_type", "created_at")
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "servings", "created_by", "updated_at")
    search_fields = ("title", "source")
    inlines = [PhotoInline]
