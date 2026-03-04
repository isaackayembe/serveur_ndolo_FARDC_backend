from django.urls import path
from .views import (
    admin_activities,
    carte_detail,
    cartes_collection,
    cartes_stats,
    list_grades,
    login_user,
    logout_user,
    me,
    register_user,
)

urlpatterns = [
    path("admin/activities/", admin_activities, name="admin-activities"),
    path("auth/register/", register_user, name="auth-register"),
    path("auth/login/", login_user, name="auth-login"),
    path("auth/me/", me, name="auth-me"),
    path("auth/logout/", logout_user, name="auth-logout"),
    path("cartes/grades/", list_grades, name="list-grades"),
    path("cartes/stats/", cartes_stats, name="cartes-stats"),
    path("cartes/<int:carte_id>/", carte_detail, name="carte-detail"),
    path("cartes/", cartes_collection, name="cartes-collection"),
]
