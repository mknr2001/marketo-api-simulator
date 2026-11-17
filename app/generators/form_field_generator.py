"""FormFields generator producing PHP-serialized associative arrays."""

from __future__ import annotations

import random
from typing import Any

from app.generators.lead_generator import JOB_TITLES
from app.generators.php_serializer import php_serialize_array

PRODUCT_HIERARCHY = [
    {
        "family": "Mobile",
        "group": "Business Mobile",
        "product": "Business Mobile Plan",
    },
    {
        "family": "Broadband",
        "group": "Business Broadband",
        "product": "Business Broadband Plus",
    },
    {
        "family": "Voice",
        "group": "Cloud Voice",
        "product": "Hosted Voice Solution",
    },
    {
        "family": "Security",
        "group": "Cyber Security",
        "product": "Endpoint Protection Suite",
    },
    {
        "family": "Networking",
        "group": "Connected Workplace",
        "product": "Managed SD-WAN",
    },
]

CALLBACK_TIMES = ["9am - 12pm", "12pm - 2pm", "2pm - 5pm", "Anytime"]
MOBILE_BRANDS = ["ExampleTel", "SampleMobile", "DemoNet", "TestComms"]

MRFS_BRANDS = ["BT", "EE", "Plusnet", "BT Business", "BT Enterprise"]
MRFS_CONSENT_CHANNELS = ["Email", "Phone", "SMS", "Email,Phone", "Digital"]
MRFS_CONSENT_TYPES = ["Opt-in", "Explicit", "Implied", "Marketing", "Opt-out"]
MRFS_COUNTRIES = ["United Kingdom", "GB", "UK", "Ireland", "United States", "Germany", "France"]


def generate_mrfs_attribute_pairs(rng: random.Random) -> list[tuple[str, Any]]:
    """Generate realistic mRFSBrand, mRFSConsentChannel, mRFSConsentType, mRFSCountry pairs.

    Models diverse real-world ETL ingestion scenarios for downstream Databricks parsing:
      - Scenario 1 (30%): Full profile — all 4 fields present with valid string values
      - Scenario 2 (20%): Brand and Country present; Consent fields absent
      - Scenario 3 (15%): Brand and Consent fields present; Country absent
      - Scenario 4 (15%): Country only present (e.g. general regional contact form)
      - Scenario 5 (10%): Partial / Null values — fields present but set to None (N;) or empty string ("")
      - Scenario 6 (10%): Completely omitted — none of the 4 fields included (legacy forms)
    """
    scenario = rng.choices(
        ["full", "brand_country", "brand_consent", "country_only", "with_nulls", "omitted"],
        weights=[30, 20, 15, 15, 10, 10],
        k=1,
    )[0]

    if scenario == "omitted":
        return []

    brand = rng.choice(MRFS_BRANDS)
    country = rng.choice(MRFS_COUNTRIES)
    channel = rng.choice(MRFS_CONSENT_CHANNELS)
    ctype = rng.choice(MRFS_CONSENT_TYPES)

    pairs: list[tuple[str, Any]] = []

    if scenario == "full":
        pairs.extend([
            ("mRFSBrand", brand),
            ("mRFSConsentChannel", channel),
            ("mRFSConsentType", ctype),
            ("mRFSCountry", country),
        ])
    elif scenario == "brand_country":
        pairs.extend([
            ("mRFSBrand", brand),
            ("mRFSCountry", country),
        ])
    elif scenario == "brand_consent":
        pairs.extend([
            ("mRFSBrand", brand),
            ("mRFSConsentChannel", channel),
            ("mRFSConsentType", ctype),
        ])
    elif scenario == "country_only":
        pairs.extend([
            ("mRFSCountry", country),
        ])
    elif scenario == "with_nulls":
        brand_val = rng.choice([brand, "", None])
        channel_val = rng.choice([channel, None, ""])
        ctype_val = rng.choice([ctype, None, ""])
        country_val = rng.choice([country, "", None])
        pairs.extend([
            ("mRFSBrand", brand_val),
            ("mRFSConsentChannel", channel_val),
            ("mRFSConsentType", ctype_val),
            ("mRFSCountry", country_val),
        ])

    return pairs


def generate_mixed_date_value(rng: random.Random) -> Any:
    """Generate mixed date values to simulate source parsing edge cases.

    Distribution:
        65% -> integer Unix timestamp
        20% -> empty string
        10% -> null (None)
        5%  -> normal date string
    """
    choice = rng.choices(["int", "empty", "null", "str"], weights=[65, 20, 10, 5], k=1)[0]
    if choice == "int":
        return rng.randint(1577836800, 1893456000)  # 2020 to 2030
    if choice == "empty":
        return ""
    if choice == "null":
        return None
    # ISO date string
    year = rng.randint(2020, 2026)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def generate_aem_comms_panel_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template A: AEM commsPanel callback form fields."""
    prod = rng.choice(PRODUCT_HIERARCHY)
    form_vid = str(rng.randint(1000000, 9999999))
    pairs: list[tuple[str, Any]] = [
        ("mRFSFormName", "commsPanel_callback"),
        ("mRFSSourceType", "AEM"),
        ("mRFSFormType", "callback"),
        ("mRFSProductFamily", prod["family"]),
        ("mRFSProductGroup", prod["group"]),
        ("mRFSProduct", prod["product"]),
        ("mRFSFirstName", str(lead["firstName"])),
        ("mRFSLastName", str(lead["lastName"])),
        ("Email", str(lead["email"])),
        ("mRFSPhone", str(lead["phone"])),
        ("mRFSCompany", str(lead["company"])),
        ("mRFSPostalCode", str(lead["postalCode"])),
        ("mRFSCallBackBetween", rng.choice(CALLBACK_TIMES)),
        ("mRFSBusinessType", str(lead["businessType"])),
        ("mRFSNumberofEmployees", str(lead["employeeBand"])),
        ("mRFSQueryString", f"prod={prod['family'].lower()}&ref=comms_panel"),
        ("formid", str(form_id)),
        ("munchkinId", "123-ABC-456"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)


def generate_aem_embedded_product_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template B: AEM embedded product callback form fields."""
    prod = rng.choice(PRODUCT_HIERARCHY)
    form_vid = str(rng.randint(1000000, 9999999))
    pairs: list[tuple[str, Any]] = [
        ("mRFSFirstName", str(lead["firstName"])),
        ("mRFSLastName", str(lead["lastName"])),
        ("Email", str(lead["email"])),
        ("mRFSPhone", str(lead["phone"])),
        ("mRFSBusinessType", str(lead["businessType"])),
        ("mRFSCompany", str(lead["company"])),
        ("mRFSNumberofEmployees", str(lead["employeeBand"])),
        ("mRFSJobTitle", rng.choice(JOB_TITLES)),
        ("mRFSPostalCode", str(lead["postalCode"])),
        ("mRFSQuery", f"Enquiry regarding {prod['product']}"),
        ("mRFSQueryDetail", f"Interested in pricing tiers for {lead['employeeBand']} seats"),
        ("mRFSCallBackBetween", rng.choice(CALLBACK_TIMES)),
        ("mRFSQueryString", f"view=embedded&cat={prod['family'].lower()}"),
        ("mRFSFormName", "embedded_product_callback"),
        ("mRFSSourceType", "AEM"),
        ("mRFSFormType", "callback"),
        ("mRFSProductFamily", prod["family"]),
        ("mRFSProductGroup", prod["group"]),
        ("mRFSProduct", prod["product"]),
        ("formid", str(form_id)),
        ("munchkinId", "123-ABC-456"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)


def generate_aem_generic_callback_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template: AEM generic callback form fields."""
    prod = rng.choice(PRODUCT_HIERARCHY)
    form_vid = str(rng.randint(1000000, 9999999))
    pairs: list[tuple[str, Any]] = [
        ("mRFSFormName", "generic_callback"),
        ("mRFSSourceType", "AEM"),
        ("mRFSFormType", "callback"),
        ("mRFSProductFamily", prod["family"]),
        ("mRFSProductGroup", prod["group"]),
        ("mRFSProduct", prod["product"]),
        ("mRFSFirstName", str(lead["firstName"])),
        ("mRFSLastName", str(lead["lastName"])),
        ("Email", str(lead["email"])),
        ("mRFSPhone", str(lead["phone"])),
        ("mRFSCompany", str(lead["company"])),
        ("mRFSPostalCode", str(lead["postalCode"])),
        ("mRFSCallBackBetween", rng.choice(CALLBACK_TIMES)),
        ("mRFSBusinessType", str(lead["businessType"])),
        ("mRFSNumberofEmployees", str(lead["employeeBand"])),
        ("mRFSQueryString", "channel=web_direct"),
        ("formid", str(form_id)),
        ("munchkinId", "123-ABC-456"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)


def generate_subscription_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template C: Subscription form fields."""
    form_vid = str(rng.randint(1000000, 9999999))
    pairs: list[tuple[str, Any]] = [
        ("mRFSFirstName", str(lead["firstName"])),
        ("mRFSLastName", str(lead["lastName"])),
        ("Email", str(lead["email"])),
        ("mRFSEmailConsentFlag", rng.choice(["true", "1", "yes"])),
        ("mRFSFormName", "newsletter_subscription"),
        ("mRFSQueryString", "source=footer_subscribe"),
        ("formid", str(form_id)),
        ("munchkinId", "123-ABC-456"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)


def generate_security_training_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template D: Security-training form fields."""
    form_vid = str(rng.randint(1000000, 9999999))
    pairs: list[tuple[str, Any]] = [
        ("Email", str(lead["email"])),
        ("mRFSEmailConsentFlag", "true"),
        ("eventData", f"course_id={rng.randint(100, 999)}&status=registered"),
        ("mRFSSourceType", "training_portal"),
        ("formid", str(form_id)),
        ("munchkinId", "123-ABC-456"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)


def generate_standard_landing_fields(
    rng: random.Random,
    lead: dict[str, Any],
    form_id: int,
    referrer_url: str,
) -> str:
    """Generate Template E: Standard Marketo landing form fields with mixed date types."""
    form_vid = str(rng.randint(1000000, 9999999))
    lp_id = str(rng.randint(1000, 9999))
    sub_id = str(rng.randint(10, 99))
    req_id = f"req_{rng.randint(100000, 999999)}"

    dob = generate_mixed_date_value(rng)
    arpu_date = generate_mixed_date_value(rng)

    pairs: list[tuple[str, Any]] = [
        ("module", "AnnualRevenue"),
        ("action", "change"),
        ("FirstName", str(lead["firstName"])),
        ("LastName", str(lead["lastName"])),
        ("Email", str(lead["email"])),
        ("activeFlag", "True" if rng.random() > 0.3 else "False"),
        ("addressQualityFlag", ""),
        ("AnnualRevenue", rng.randint(50000, 25000000)),
        ("DateofBirth", dob),
        ("arpuSnapshotDate", arpu_date),
        ("averageRevenuePerUser1Month", rng.randint(20, 500)),
        ("averageRevenuePerUser6Months", rng.randint(100, 3000)),
        ("companyCurrentMobileBrand", rng.choice(MOBILE_BRANDS)),
        ("AnonymousIP", "false"),
        ("companyAttPstnLines", rng.randint(1, 20)),
        ("Phone", str(lead["phone"])),
        ("Address", f"{rng.randint(1, 150)} Sample Industrial Estate"),
        ("mOD1", "1" if rng.random() > 0.5 else "0"),
        ("formid", str(form_id)),
        ("lpId", lp_id),
        ("subId", sub_id),
        ("munchkinId", "123-ABC-456"),
        ("lpurl", f"https://business.example.test/lp/{lp_id}"),
        ("cr", f"cr_{rng.randint(1000, 9999)}"),
        ("kw", "enterprise telecom solutions"),
        ("q", ""),
        ("_mkt_trk", f"id:123-ABC-456&token:_mch-example.test-{rng.randint(1000000000, 1999999999)}"),
        ("formVid", form_vid),
        ("_mktoReferrer", referrer_url),
        ("checksumFields", "Email,FirstName,LastName"),
        ("checksum", f"{rng.randint(10000000, 99999999):x}"),
        ("formServiceRequestId31337", req_id),
    ]
    pairs.extend(generate_mrfs_attribute_pairs(rng))
    return php_serialize_array(pairs)
