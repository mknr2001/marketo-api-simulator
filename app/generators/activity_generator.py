"""Activity records and TSV generator for Marketo Bulk Activity Export simulation."""

from __future__ import annotations

import csv
import hashlib
import io
import random
from datetime import UTC, date, datetime, time
from typing import Any

from app.generators.lead_generator import generate_lead_pool, select_lead
from app.generators.record_templates import (
    choose_primary_attribute,
    generate_client_ip,
    generate_referrer_url,
    generate_user_agent,
    select_template,
)
from app.utilities.datetime_utils import format_utc_iso, normalize_to_utc

TSV_COLUMNS = [
    "marketoGUID",
    "leadId",
    "activityDate",
    "activityTypeId",
    "primaryAttributeValueId",
    "primaryAttributeValue",
    "CAPTCHANormalizedScore",
    "CAPTCHAProvider",
    "CAPTCHARawScore",
    "ClientIPAddress",
    "FormFields",
    "mRFSBrand",
    "mRFSConsentChannel",
    "mRFSConsentType",
    "mRFSCountry",
    "ProgramName",
    "ProgramType",
    "QueryParameters",
    "ReferrerURL",
    "UserAgent",
    "WebpageID",
]


def generate_deterministic_seed(
    export_id: str,
    activity_type_ids: list[int] | str,
    start_at: datetime,
    end_at: datetime,
) -> int:
    """Generate reproducible integer seed from canonical export parameters.

    Canonical seed string:
        <exportId>|2|<startAt-UTC>|<endAt-UTC>|TSV
    """
    act_id_str = "2"
    start_iso = format_utc_iso(start_at)
    end_iso = format_utc_iso(end_at)
    canonical = f"{export_id}|{act_id_str}|{start_iso}|{end_iso}|TSV"
    digest = hashlib.sha256(canonical.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def calculate_daily_record_counts(
    rng: random.Random,
    num_days: int,
    min_per_day: int,
    max_per_day: int,
) -> list[int]:
    """Calculate deterministic daily record counts using job-scoped RNG."""
    return [rng.randint(min_per_day, max_per_day) for _ in range(num_days)]


def _generate_day_timestamp(
    rng: random.Random,
    target_date: date,
    start_at: datetime,
    end_at: datetime,
) -> datetime:
    """Generate a random UTC timestamp within the exact daily boundary."""
    utc_start = normalize_to_utc(start_at)
    utc_end = normalize_to_utc(end_at)

    day_start = datetime.combine(target_date, time.min, tzinfo=UTC)
    day_end = datetime.combine(target_date, time.max, tzinfo=UTC)

    # Apply global boundaries to clamp the daily window
    lower_bound = max(day_start, utc_start)
    upper_bound = min(day_end, utc_end)

    lower_ts = lower_bound.timestamp()
    upper_ts = upper_bound.timestamp()

    selected_ts = lower_ts if upper_ts <= lower_ts else rng.uniform(lower_ts, upper_ts)

    # Truncate fractional seconds to integer seconds
    dt = datetime.fromtimestamp(int(selected_ts), tz=UTC)
    # Ensure it stays within bounds
    if dt < utc_start:
        dt = utc_start
    if dt > utc_end:
        dt = utc_end
    return dt


def generate_activity_records(
    export_id: str,
    seed: int,
    start_at: datetime,
    end_at: datetime,
    daily_counts: list[int],
    daily_dates: list[date],
) -> list[dict[str, Any]]:
    """Generate deterministic activity records matching the 21-column schema.

    Sorted by (activityDate ASC, marketoGUID ASC).
    """
    rng = random.Random(seed)
    lead_pool = generate_lead_pool(rng, size=40)

    # Base GUID offset for numeric marketoGUID
    base_guid = 86000000 + rng.randint(10000, 99999)
    guid_counter = 0

    records: list[dict[str, Any]] = []

    for day_idx, current_date in enumerate(daily_dates):
        count_for_day = daily_counts[day_idx]
        for _ in range(count_for_day):
            guid_counter += 1
            guid = str(base_guid + guid_counter)

            lead = select_lead(rng, lead_pool)
            template = select_template(rng)
            act_date = _generate_day_timestamp(rng, current_date, start_at, end_at)
            date_str = format_utc_iso(act_date)

            prim_id, prim_val = choose_primary_attribute(rng)
            ref_url = generate_referrer_url(rng)
            form_fields_str = template.field_generator(rng, lead, prim_id, ref_url)

            client_ip = generate_client_ip(rng, template)
            user_agent = generate_user_agent(rng, template)
            brand = template.brand

            webpage_id = str(rng.randint(*template.webpage_id_range))

            # QueryParameters: literal '{}' or None or synthetic query
            qp_choice = rng.choices(["json", "null", "query"], weights=[70, 20, 10], k=1)[0]
            if qp_choice == "json":
                query_params: str | None = "{}"
            elif qp_choice == "query":
                query_params = f"utm_source=google&utm_medium=cpc&utm_campaign=brand_{str(lead['businessType']).lower()}"
            else:
                query_params = None

            # CAPTCHA scores normally None (null)
            captcha_norm: str | None = None
            captcha_prov: str | None = None
            captcha_raw: str | None = None

            # Optional 2% chance of CAPTCHA populated
            if rng.random() < 0.02:
                captcha_prov = "reCAPTCHA"
                captcha_raw = f"{rng.uniform(0.1, 0.9):.2f}"
                captcha_norm = captcha_raw

            record = {
                "marketoGUID": guid,
                "leadId": str(lead["leadId"]),
                "activityDate": date_str,
                "activityTypeId": "2",
                "primaryAttributeValueId": str(prim_id),
                "primaryAttributeValue": prim_val,
                "CAPTCHANormalizedScore": captcha_norm,
                "CAPTCHAProvider": captcha_prov,
                "CAPTCHARawScore": captcha_raw,
                "ClientIPAddress": client_ip,
                "FormFields": form_fields_str,
                "mRFSBrand": None,
                "mRFSConsentChannel": None,
                "mRFSConsentType": None,
                "mRFSCountry": None,
                "ProgramName": None,
                "ProgramType": None,
                "QueryParameters": query_params,
                "ReferrerURL": ref_url,
                "UserAgent": user_agent,
                "WebpageID": webpage_id,
            }
            records.append(record)

    # Sort records: 1. activityDate ascending, 2. marketoGUID ascending
    records.sort(key=lambda r: (r["activityDate"], int(r["marketoGUID"])))
    return records


def generate_tsv_bytes(records: list[dict[str, Any]], columns: list[str] = TSV_COLUMNS) -> bytes:
    """Generate TSV bytes from records using csv.writer.

    Rules:
    - Delimiter: horizontal tab, \t
    - Record delimiter: Unix newline, \n
    - Encoding: UTF-8 without BOM
    - Header: exactly one header for non-empty records; empty bytes for 0 records
    - None/empty values: empty string between tabs
    """
    if not records:
        return b""

    output = io.StringIO()
    writer = csv.writer(
        output,
        delimiter="\t",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # Header
    writer.writerow(columns)

    # Data rows
    for rec in records:
        row = ["" if rec.get(col) is None else str(rec[col]) for col in columns]
        writer.writerow(row)

    return output.getvalue().encode("utf-8")
