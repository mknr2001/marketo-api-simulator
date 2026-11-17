"""Record templates registry with deterministic weighted selection."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.generators.form_field_generator import (
    generate_aem_comms_panel_fields,
    generate_aem_embedded_product_fields,
    generate_aem_generic_callback_fields,
    generate_security_training_fields,
    generate_standard_landing_fields,
    generate_subscription_fields,
)

DOCUMENTATION_IPS = [
    "192.0.2.14",
    "192.0.2.45",
    "192.0.2.88",
    "198.51.100.12",
    "198.51.100.73",
    "198.51.100.120",
    "203.0.113.19",
    "203.0.113.56",
    "203.0.113.91",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

REFERRER_PATHS = [
    "business-mobile/devices/samsung/",
    "business-broadband/fibre-broadband/",
    "cloud-voice/hosted-voip/",
    "security/managed-firewall/",
    "business/plans-and-pricing/",
    "solutions/enterprise-connectivity/",
]


@dataclass(frozen=True)
class RecordTemplate:
    """Configuration for a specific Marketo activity record template."""

    name: str
    weight: int
    field_generator: Callable[[random.Random, dict[str, Any], int, str], str]
    is_aem: bool
    brand: str | None
    webpage_id_range: tuple[int, int]
    default_query_params: str = "{}"


TEMPLATES: list[RecordTemplate] = [
    RecordTemplate(
        name="aem_comms_panel_callback",
        weight=25,
        field_generator=generate_aem_comms_panel_fields,
        is_aem=True,
        brand="BT",
        webpage_id_range=(17000, 17999),
    ),
    RecordTemplate(
        name="aem_embedded_product_callback",
        weight=35,
        field_generator=generate_aem_embedded_product_fields,
        is_aem=True,
        brand="BT",
        webpage_id_range=(18000, 18999),
    ),
    RecordTemplate(
        name="aem_generic_callback",
        weight=15,
        field_generator=generate_aem_generic_callback_fields,
        is_aem=True,
        brand="BT",
        webpage_id_range=(19000, 19999),
    ),
    RecordTemplate(
        name="subscription_form",
        weight=10,
        field_generator=generate_subscription_fields,
        is_aem=False,
        brand=None,
        webpage_id_range=(20000, 20999),
    ),
    RecordTemplate(
        name="security_training_form",
        weight=5,
        field_generator=generate_security_training_fields,
        is_aem=False,
        brand=None,
        webpage_id_range=(21000, 21999),
    ),
    RecordTemplate(
        name="standard_marketo_landing_form",
        weight=10,
        field_generator=generate_standard_landing_fields,
        is_aem=False,
        brand=None,
        webpage_id_range=(30000, 39999),
    ),
]


def select_template(rng: random.Random) -> RecordTemplate:
    """Select a template deterministically according to defined weights."""
    weights = [t.weight for t in TEMPLATES]
    return rng.choices(TEMPLATES, weights=weights, k=1)[0]


def choose_primary_attribute(rng: random.Random) -> tuple[int, str]:
    """Select primaryAttributeValueId and corresponding value with 80/20 weight.

    1029 -> 80% : AEM·Form·Testing.AEM·Form·Testing
    1356 -> 20% : FillOutForm-Testing.01_filloutform
    """
    choice = rng.choices([1029, 1356], weights=[80, 20], k=1)[0]
    if choice == 1029:
        return 1029, "AEM·Form·Testing.AEM·Form·Testing"
    return 1356, "FillOutForm-Testing.01_filloutform"


def generate_referrer_url(rng: random.Random) -> str:
    """Generate a synthetic Referrer URL under example.test domains without anchor tags."""
    base = rng.choice(["https://business.example.test/", "https://marketo.example.test/"])
    path = rng.choice(REFERRER_PATHS)
    return f"{base}{path}"


def generate_client_ip(rng: random.Random, template: RecordTemplate) -> str | None:
    """Return ClientIPAddress: None for AEM, synthetic doc-range IP for landing forms."""
    if template.is_aem:
        return None
    return rng.choice(DOCUMENTATION_IPS)


def generate_user_agent(rng: random.Random, template: RecordTemplate) -> str | None:
    """Return UserAgent: None for AEM, realistic browser string for standard landing forms."""
    if template.is_aem:
        return None
    return rng.choice(USER_AGENTS)
