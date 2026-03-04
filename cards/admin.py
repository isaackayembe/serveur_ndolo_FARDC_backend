from django.contrib import admin
from .models import ActivityLog, Carte


@admin.register(Carte)
class CarteAdmin(admin.ModelAdmin):
    list_display = ("id", "numero", "nom", "post_nom", "prenom", "grade", "matricule", "date")
    search_fields = ("numero", "nom", "post_nom", "prenom", "matricule", "grade")
    list_filter = ("grade", "date")
    readonly_fields = ("numero", "image")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "user", "carte", "created_at")
    search_fields = ("action", "details", "user__username", "carte__numero")
    list_filter = ("action", "created_at")
    readonly_fields = ("action", "details", "user", "carte", "created_at")
