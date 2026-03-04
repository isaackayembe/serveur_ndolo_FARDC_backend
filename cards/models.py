from django.db import models
from django.contrib.auth.models import User


class Carte(models.Model):
    class GradeChoices(models.TextChoices):
        LT_COL = "Lt Col", "Lt Col"
        COL = "Col", "Col"
        LT = "Lt", "Lt"
        SLT = "SLt", "SLt"
        SOFFR = "SOFFR", "SOFFR"
        ONE_CL = "1Cl", "1Cl"
        TWO_CL = "2Cl", "2Cl"
        CPL = "Cpl", "Cpl"
        ADJ_CHEF = "AdjChef", "AdjChef"
        SRG_MAJ = "SrgMaj", "SrgMaj"
        CAP = "Cap", "Cap"
        MAJ = "Maj", "Maj"

    nom = models.CharField(max_length=100)
    post_nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    grade = models.CharField(max_length=20, choices=GradeChoices.choices)
    matricule = models.CharField(max_length=100, unique=True)
    fonction = models.CharField(max_length=150)
    date = models.CharField(max_length=50)
    numero = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    profil = models.ImageField(upload_to="profils/", null=True, blank=True)
    image = models.ImageField(upload_to="cartes/", null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.numero:
            self.numero = str(self.id)
            super().save(update_fields=["numero"])

    def __str__(self):
        return f"{self.nom} {self.post_nom} {self.prenom}"


class ActivityLog(models.Model):
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    carte = models.ForeignKey(
        Carte,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.created_at:%Y-%m-%d %H:%M:%S}"
