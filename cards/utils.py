from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

OFFICIER_GRADES = {"Cap", "Lt", "SLt"}
OFFICIER_SUPERIEUR_GRADES = {"Col", "Lt Col", "Maj"}
SOUS_OFFICIER_GRADES = {"1Cl", "2Cl", "Cpl", "AdjChef", "SrgMaj", "SOFFR"}

TEMPLATE_FILES_BY_CATEGORY = {
    "officier": [
        "carte_officier.png",
        "carte_vierge_officier.png",
        "officier.png",
    ],
    "officier_superieur": [
        "carte_officier_superieur.png",
        "carte_vierge_officier_superieur.png",
        "officier_superieur.png",
    ],
    "sous_officier": [
        "carte_sous_officier.png",
        "carte_vierge_sous_officier.png",
        "sous_officier.png",
    ],
}


def _load_font(size: int = 40) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _get_grade_category(grade: str) -> str:
    normalized = str(grade).strip()
    if normalized in OFFICIER_GRADES:
        return "officier"
    if normalized in OFFICIER_SUPERIEUR_GRADES:
        return "officier_superieur"
    if normalized in SOUS_OFFICIER_GRADES:
        return "sous_officier"
    return "sous_officier"


def _resolve_template_path(category: str) -> Path | None:
    templates_dir = Path(settings.MEDIA_ROOT) / "templates"
    for filename in TEMPLATE_FILES_BY_CATEGORY.get(category, []):
        path = templates_dir / filename
        if path.exists():
            return path

    legacy = templates_dir / "carte_vierge.png"
    if legacy.exists():
        return legacy

    return None


def _paste_profile_photo(image: Image.Image, profil_path: str | None) -> None:
    if not profil_path:
        return

    path = Path(profil_path)
    if not path.exists():
        return

    try:
        with Image.open(path) as profil_img:
            profil = profil_img.convert("RGB").resize((220, 260))
            image.paste(profil, (60, 140))
    except OSError:
        return


def generer_carte(
    nom: str,
    numero: str,
    date: str,
    grade: str,
    profil_path: str | None = None,
) -> bytes:
    category = _get_grade_category(grade)
    template_path = _resolve_template_path(category)

    if template_path:
        image = Image.open(template_path).convert("RGB")
    else:
        # Fallback to a blank card if template file is missing.
        image = Image.new("RGB", (1200, 700), "white")

    _paste_profile_photo(image, profil_path)

    draw = ImageDraw.Draw(image)
    font = _load_font(40)

    draw.text((200, 150), str(nom), fill="black", font=font)
    draw.text((200, 220), str(numero), fill="black", font=font)
    draw.text((200, 290), str(date), fill="black", font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
