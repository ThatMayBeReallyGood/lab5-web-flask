import base64
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from PIL import Image, ImageOps, UnidentifiedImageError

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")


def validate_image_file(file) -> str | None:
    if file is None or not file.filename:
        return "Файл изображения не выбран."
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return "Допустимы только файлы PNG, JPG, JPEG, GIF, BMP или WEBP."
    file.stream.seek(0)
    try:
        with Image.open(file.stream) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        return "Файл поврежден или не является изображением."
    file.stream.seek(0)
    return None


def validate_period(period_text: str) -> tuple[float | None, str | None]:
    try:
        period = float(period_text)
    except (TypeError, ValueError):
        return None, "Период должен быть числом."
    if not np.isfinite(period) or period < 2 or period > 1000:
        return None, "Период должен находиться в диапазоне от 2 до 1000 пикселей."
    return period, None


def periodic_image(image: Image.Image, period: float, function_name: str) -> Image.Image:
    rgb = np.asarray(ImageOps.exif_transpose(image).convert("RGB"), dtype=np.float32)
    height, width = rgb.shape[:2]
    x = np.arange(width, dtype=np.float32)[None, :]
    y = np.arange(height, dtype=np.float32)[:, None]

    angle = 2 * np.pi * ((x / period) + (y / period))
    wave = np.sin(angle) if function_name == "sin" else np.cos(angle)
    multiplier = (wave + 1.0) / 2.0
    result = np.clip(rgb * multiplier[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def build_histogram(image: Image.Image) -> str:
    rgb = np.asarray(image.convert("RGB"))
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=120)
    for channel, color in enumerate(("red", "green", "blue")):
        ax.hist(rgb[:, :, channel].ravel(), bins=256, range=(0, 256),
                color=color, alpha=0.55, label=color.upper())
    ax.set_title("Распределение каналов RGB")
    ax.set_xlabel("Интенсивность")
    ax.set_ylabel("Количество пикселей")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.2)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def verify_recaptcha(user_response: str) -> tuple[bool, str]:
    if not RECAPTCHA_SECRET_KEY:
        return True, "Капча пропущена: секретный ключ не настроен."
    if not user_response:
        return False, "Подтвердите, что вы не робот."
    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET_KEY, "response": user_response},
            timeout=5,
        )
        result = response.json()
    except (requests.RequestException, ValueError):
        return False, "Сервис проверки капчи временно недоступен."
    if result.get("success"):
        return True, "Капча пройдена."
    return False, "Капча не пройдена. Повторите проверку."


def image_data_uri(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    results = None

    if request.method == "POST":
        uploaded_file = request.files.get("image")
        period_text = request.form.get("period", "")
        function_name = request.form.get("function", "sin")

        if function_name not in {"sin", "cos"}:
            error = "Выберите функцию sin или cos."
        else:
            error = validate_image_file(uploaded_file)
            if error is None:
                period, period_error = validate_period(period_text)
                if period_error:
                    error = period_error

        if error is None:
            captcha_ok, captcha_message = verify_recaptcha(
                request.form.get("g-recaptcha-response", "")
            )
            if not captcha_ok:
                error = captcha_message

        if error is None:
            try:
                original = ImageOps.exif_transpose(Image.open(uploaded_file.stream)).convert("RGB")
                processed = periodic_image(original, period, function_name)
                results = {
                    "original": image_data_uri(original),
                    "processed": image_data_uri(processed),
                    "original_histogram": build_histogram(original),
                    "processed_histogram": build_histogram(processed),
                    "period": period,
                    "function": function_name,
                    "classification": (
                        "Классификация нейросетью не включена: в варианте 19 обработка выполняется "
                        "детерминированным численным методом."
                    ),
                }
            except (UnidentifiedImageError, OSError, ValueError) as exception:
                error = f"Не удалось обработать изображение: {exception}"

    return render_template(
        "index.html",
        error=error,
        results=results,
        recaptcha_site_key=RECAPTCHA_SITE_KEY,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
