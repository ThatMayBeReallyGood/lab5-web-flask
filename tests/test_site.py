import io

import numpy as np
from PIL import Image

import app as app_module


site = app_module


def test_periodic_image_preserves_size_and_rgb_mode():
    source = Image.fromarray(
        np.full((32, 48, 3), 180, dtype=np.uint8),
        mode="RGB",
    )

    result = site.periodic_image(source, 12.0, "sin")

    assert result.size == source.size
    assert result.mode == "RGB"
    pixels = np.asarray(result)
    assert pixels.min() >= 0
    assert pixels.max() <= 255


def test_build_histogram_returns_png_base64():
    source = Image.fromarray(
        np.zeros((20, 20, 3), dtype=np.uint8),
        mode="RGB",
    )

    encoded = site.build_histogram(source)

    assert encoded
    assert encoded.startswith("iVBOR")
    assert len(encoded) > 100


def test_validation_rejects_bad_extension_and_period():
    assert site.validate_period("abc")[1] == "Период должен быть числом."
    assert site.validate_period("1")[1] == "Период должен находиться в диапазоне от 2 до 1000 пикселей."

    class Upload:
        filename = "document.txt"

    assert "Допустимы" in site.validate_image_file(Upload())


def test_post_accepts_valid_image_when_captcha_is_not_configured(monkeypatch):
    monkeypatch.setattr(site, "RECAPTCHA_SECRET_KEY", "")
    client = site.app.test_client()
    image_buffer = io.BytesIO()
    Image.new("RGB", (24, 24), (120, 80, 40)).save(image_buffer, format="PNG")
    image_buffer.seek(0)

    response = client.post(
        "/",
        data={
            "image": (image_buffer, "test.png"),
            "period": "20",
            "function": "cos",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"\xd0\xa0\xd0\xb5\xd0\xb7\xd1\x83\xd0\xbb\xd1\x8c\xd1\x82\xd0\xb0\xd1\x82" in response.data
