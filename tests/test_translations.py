"""Every enum value a sensor can show needs a label in each shipped language."""
import json
from pathlib import Path

import pytest

from custom_components.spirala_heat_pump.const import (
    ACTIVE_CIRCUIT_ENUM,
    ERROR_ENUM,
    NOT_RUNNING_ENUM,
)

TRANSLATIONS = Path(__file__).parents[1] / "custom_components" / "spirala_heat_pump" / "translations"
ENUMS = {
    "error_code": ERROR_ENUM,
    "not_running_reason": NOT_RUNNING_ENUM,
    "active_circuit": ACTIVE_CIRCUIT_ENUM,
}


@pytest.mark.parametrize("lang", ["en", "cs"])
@pytest.mark.parametrize("sensor", sorted(ENUMS))
def test_enum_values_are_translated(lang, sensor):
    data = json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8"))
    labels = data["entity"]["sensor"][sensor].get("state", {})
    missing = sorted(set(ENUMS[sensor].values()) - set(labels))
    assert not missing, f"{lang}: {sensor} has no label for {missing}"


@pytest.mark.parametrize("sensor", sorted(ENUMS))
def test_enum_values_are_valid_translation_keys(sensor):
    # hassfest: [a-z0-9-_]+, no leading/trailing hyphen or underscore
    import re
    for value in ENUMS[sensor].values():
        assert re.fullmatch(r"[a-z0-9]([a-z0-9_-]*[a-z0-9])?", value), value
