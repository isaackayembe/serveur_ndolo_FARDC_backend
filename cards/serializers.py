from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Carte
from .models import ActivityLog


class CarteSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    profil_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Carte
        fields = [
            "id",
            "nom",
            "post_nom",
            "prenom",
            "grade",
            "matricule",
            "fonction",
            "date",
            "numero",
            "profil",
            "profil_url",
            "image_url",
        ]
        read_only_fields = ["id", "numero", "profil_url", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_profil_url(self, obj):
        if not obj.profil:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.profil.url)
        return obj.profil.url


class RegisterSerializer(serializers.Serializer):
    matricule = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    nom = serializers.CharField(max_length=150, required=False, allow_blank=True)
    post_nom = serializers.CharField(max_length=150, required=False, allow_blank=True)
    prenom = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_matricule(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce matricule existe deja.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        matricule = validated_data["matricule"]
        password = validated_data["password"]
        prenom = validated_data.get("prenom", "")
        nom = validated_data.get("nom", "")
        post_nom = validated_data.get("post_nom", "")

        last_name = f"{nom} {post_nom}".strip()
        return User.objects.create_user(
            username=matricule,
            password=password,
            first_name=prenom,
            last_name=last_name,
        )


class LoginSerializer(serializers.Serializer):
    matricule = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class ActivityLogSerializer(serializers.ModelSerializer):
    user_matricule = serializers.SerializerMethodField()
    carte_numero = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "action",
            "details",
            "created_at",
            "user_matricule",
            "carte_numero",
            "carte",
            "user",
        ]

    def get_user_matricule(self, obj):
        return obj.user.username if obj.user else None

    def get_carte_numero(self, obj):
        return obj.carte.numero if obj.carte else None
