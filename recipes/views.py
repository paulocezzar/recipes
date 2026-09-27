import json
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import Photo, Recipe
from .reader import ReaderError
from .reader import read_recipe as run_reader

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024
MAX_PHOTOS_PER_RECIPE = 6


def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Your session has ended. Sign in again."}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def _text(value, limit=None):
    s = "" if value is None else str(value).strip()
    return s[:limit] if limit else s


def _clean(payload):
    """Validate and normalise a recipe body from the browser."""
    ingredients = []
    for g in payload.get("ingredients") or []:
        if not isinstance(g, dict):
            continue
        items = [
            {"qty": _text(i.get("qty"), 60), "item": _text(i.get("item"), 500)}
            for i in (g.get("items") or [])
            if isinstance(i, dict) and (_text(i.get("qty")) or _text(i.get("item")))
        ]
        if items or _text(g.get("heading")):
            ingredients.append({"heading": _text(g.get("heading"), 120), "items": items})
    method = []
    for g in payload.get("method") or []:
        if not isinstance(g, dict):
            continue
        steps = [_text(s, 4000) for s in (g.get("steps") or []) if _text(s)]
        if steps or _text(g.get("heading")):
            method.append({"heading": _text(g.get("heading"), 120), "steps": steps})
    return {
        "title": _text(payload.get("title"), 200) or "Untitled recipe",
        "description": _text(payload.get("description"), 2000),
        "servings": _text(payload.get("servings"), 60),
        "prep": _text(payload.get("prep"), 60),
        "cook": _text(payload.get("cook"), 60),
        "ingredients": ingredients,
        "method": method,
        "notes": _text(payload.get("notes"), 8000),
        "source": _text(payload.get("source"), 300),
    }


def _body(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


@login_required
def home(request):
    return render(request, "recipes/app.html")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


@api_login_required
@require_http_methods(["GET", "POST"])
def recipes_collection(request):
    if request.method == "GET":
        qs = Recipe.objects.select_related("created_by").prefetch_related("photos")
        return JsonResponse({"recipes": [r.to_dict() for r in qs]})
    payload = _body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid recipe data."}, status=400)
    recipe = Recipe.objects.create(created_by=request.user, **_clean(payload))
    return JsonResponse({"recipe": recipe.to_dict()}, status=201)


@api_login_required
@require_http_methods(["PUT", "DELETE"])
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "DELETE":
        recipe.delete()
        return JsonResponse({"ok": True})
    payload = _body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid recipe data."}, status=400)
    for key, value in _clean(payload).items():
        setattr(recipe, key, value)
    recipe.save()
    return JsonResponse({"recipe": recipe.to_dict()})


@api_login_required
@require_http_methods(["POST"])
def recipe_photos(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    files = request.FILES.getlist("photos")
    if not files:
        return JsonResponse({"error": "No photo was sent."}, status=400)
    existing = recipe.photos.count()
    if existing + len(files) > MAX_PHOTOS_PER_RECIPE:
        return JsonResponse({"error": f"A recipe can have up to {MAX_PHOTOS_PER_RECIPE} photos."}, status=400)
    with transaction.atomic():
        for i, f in enumerate(files):
            if f.content_type not in IMAGE_TYPES or f.size > MAX_PHOTO_BYTES:
                return JsonResponse({"error": "Photos must be JPEG, PNG or WebP and under 8 MB."}, status=400)
            Photo.objects.create(recipe=recipe, data=f.read(), content_type=f.content_type, position=existing + i)
    recipe.refresh_from_db()
    return JsonResponse({"recipe": recipe.to_dict()}, status=201)


@api_login_required
@require_http_methods(["DELETE"])
def photo_delete(request, pk):
    get_object_or_404(Photo, pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
def photo_file(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    resp = HttpResponse(bytes(photo.data), content_type=photo.content_type)
    resp["Cache-Control"] = "private, max-age=31536000, immutable"
    return resp


@api_login_required
@require_http_methods(["POST"])
def read_recipe(request):
    files = request.FILES.getlist("photos")[:MAX_PHOTOS_PER_RECIPE]
    text = _text(request.POST.get("text"))
    if not files and not text:
        return JsonResponse({"error": "Add a photo or paste some text first."}, status=400)
    images = []
    for f in files:
        if f.content_type not in IMAGE_TYPES or f.size > MAX_PHOTO_BYTES:
            return JsonResponse({"error": "Photos must be JPEG, PNG or WebP and under 8 MB."}, status=400)
        images.append((f.read(), f.content_type))
    try:
        data = run_reader(images, text)
    except ReaderError as exc:
        return JsonResponse({"error": exc.message}, status=exc.status)
    if data.get("error"):
        return JsonResponse({"error": f"Couldn't find a recipe: {data['error']}. Try a clearer photo."}, status=422)
    return JsonResponse({"recipe": _clean(data)})
