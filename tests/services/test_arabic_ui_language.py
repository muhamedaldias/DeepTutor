"""Regression: Arabic must be a valid, persisted UI language."""

from deeptutor.api.routers.settings import UISettingsUpdate
from deeptutor.services.settings.interface_settings import _normalize_language


def test_arabic_is_a_valid_ui_language():
    update = UISettingsUpdate(language="ar")
    assert update.language == "ar"
    assert update.model_dump(exclude_unset=True) == {"language": "ar"}


def test_arabic_language_code_normalizes_to_ar():
    assert _normalize_language("ar") == "ar"
    assert _normalize_language("العربية") == "ar"
    assert _normalize_language("Arabic") == "ar"


def test_korean_is_a_valid_ui_language():
    assert UISettingsUpdate(language="ko").language == "ko"
    assert _normalize_language("ko") == "ko"
