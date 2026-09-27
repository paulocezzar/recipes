from django.conf import settings
from django.db import models


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    servings = models.CharField(max_length=60, blank=True)
    prep = models.CharField(max_length=60, blank=True)
    cook = models.CharField(max_length=60, blank=True)
    # [{"heading": str, "items": [{"qty": str, "item": str}]}]
    ingredients = models.JSONField(default=list, blank=True)
    # [{"heading": str, "steps": [str]}]
    method = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="recipes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def to_dict(self):
        return {
            "id": str(self.pk),
            "title": self.title,
            "description": self.description,
            "servings": self.servings,
            "prep": self.prep,
            "cook": self.cook,
            "ingredients": self.ingredients or [],
            "method": self.method or [],
            "notes": self.notes,
            "source": self.source,
            "photos": [str(p.pk) for p in self.photos.all()],
            "createdBy": self.created_by.get_username() if self.created_by else "",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Photo(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="photos")
    data = models.BinaryField()
    content_type = models.CharField(max_length=40, default="image/jpeg")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return f"Photo {self.pk} of {self.recipe}"
