from django.core.files.base import ContentFile
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.decorators import parser_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import ActivityLog, Carte
from .serializers import (
    ActivityLogSerializer,
    CarteSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from .utils import generer_carte


def _log_activity(action: str, details: str = "", user=None, carte: Carte | None = None):
    ActivityLog.objects.create(action=action, details=details, user=user, carte=carte)


def _save_card_image(carte: Carte) -> None:
    nom_complet = f"{carte.nom} {carte.post_nom} {carte.prenom}"
    profil_path = carte.profil.path if carte.profil else None
    image_bytes = generer_carte(
        nom_complet,
        carte.numero,
        carte.date,
        carte.grade,
        profil_path=profil_path,
    )
    carte.image.save(f"carte_{carte.id}.png", ContentFile(image_bytes), save=True)


@api_view(["GET"])
def list_grades(request):
    grades = [choice[0] for choice in Carte.GradeChoices.choices]
    return Response({"grades": grades}, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    _log_activity(
        action="USER_REGISTERED",
        details=f"Utilisateur cree: {user.username}",
        user=request.user,
    )

    return Response(
        {
            "message": "Inscription reussie",
            "token": token.key,
            "user": {
                "id": user.id,
                "matricule": user.username,
                "prenom": user.first_name,
                "nom_complet": user.last_name,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    matricule = serializer.validated_data["matricule"]
    password = serializer.validated_data["password"]
    user = authenticate(username=matricule, password=password)

    if not user:
        _log_activity(
            action="LOGIN_FAILED",
            details=f"Tentative echouee pour matricule: {matricule}",
        )
        return Response(
            {"detail": "Matricule ou mot de passe invalide."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token, _ = Token.objects.get_or_create(user=user)
    _log_activity(action="LOGIN_SUCCESS", details="Connexion reussie", user=user)
    return Response(
        {
            "message": "Connexion reussie",
            "token": token.key,
            "user": {
                "id": user.id,
                "matricule": user.username,
                "prenom": user.first_name,
                "nom_complet": user.last_name,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response(
        {
            "id": user.id,
            "matricule": user.username,
            "prenom": user.first_name,
            "nom_complet": user.last_name,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    if request.auth:
        request.auth.delete()
    _log_activity(action="LOGOUT", details="Deconnexion", user=request.user)
    return Response({"message": "Deconnexion reussie"}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def cartes_collection(request):
    if request.method == "GET":
        queryset = Carte.objects.all().order_by("-id")

        grade = request.query_params.get("grade")
        matricule = request.query_params.get("matricule")
        numero = request.query_params.get("numero")
        date = request.query_params.get("date")
        search = request.query_params.get("search")

        if grade:
            queryset = queryset.filter(grade=grade)
        if matricule:
            queryset = queryset.filter(matricule__icontains=matricule)
        if numero:
            queryset = queryset.filter(numero=numero)
        if date:
            queryset = queryset.filter(date=date)
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search)
                | Q(post_nom__icontains=search)
                | Q(prenom__icontains=search)
                | Q(matricule__icontains=search)
                | Q(fonction__icontains=search)
            )

        serializer = CarteSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = CarteSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    carte = serializer.save()
    _save_card_image(carte)
    actor = request.user if request.user.is_authenticated else None
    _log_activity(
        action="CARTE_CREATED",
        details=f"Carte creee: {carte.numero}",
        user=actor,
        carte=carte,
    )

    return Response(
        {
            "message": "Carte creee",
            "carte": CarteSerializer(carte, context={"request": request}).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH", "PUT"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def carte_detail(request, carte_id: int):
    carte = get_object_or_404(Carte, id=carte_id)

    if request.method == "GET":
        serializer = CarteSerializer(carte, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    partial = request.method == "PATCH"
    serializer = CarteSerializer(
        carte,
        data=request.data,
        partial=partial,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    carte = serializer.save()
    _save_card_image(carte)
    actor = request.user if request.user.is_authenticated else None
    _log_activity(
        action="CARTE_UPDATED",
        details=f"Carte modifiee: {carte.numero}",
        user=actor,
        carte=carte,
    )

    return Response(
        {
            "message": "Carte mise a jour",
            "carte": CarteSerializer(carte, context={"request": request}).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def cartes_stats(request):
    by_grade = (
        Carte.objects.values("grade")
        .annotate(total=Count("id"))
        .order_by("grade")
    )
    total = Carte.objects.count()
    return Response(
        {
            "total_cartes": total,
            "par_grade": list(by_grade),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def admin_activities(request):
    queryset = ActivityLog.objects.select_related("user", "carte").all()

    action = request.query_params.get("action")
    matricule = request.query_params.get("matricule")
    numero = request.query_params.get("numero")

    if action:
        queryset = queryset.filter(action=action)
    if matricule:
        queryset = queryset.filter(user__username__icontains=matricule)
    if numero:
        queryset = queryset.filter(carte__numero=numero)

    serializer = ActivityLogSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
