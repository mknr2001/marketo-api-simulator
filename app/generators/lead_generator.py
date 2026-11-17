"""Deterministic synthetic lead pool generation."""

from __future__ import annotations

import random

# Synthetic first names
_FIRST_NAMES = [
    "Sample", "Test", "Demo", "Example", "Mock",
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
    "Zeta", "Eta", "Theta", "Iota", "Kappa",
    "Lambda", "Sigma", "Omega", "Nova", "Nexus",
]

# Synthetic last names
_LAST_NAMES = [
    "User", "Account", "Contact", "Person", "Client",
    "Tester", "Runner", "Builder", "Handler", "Worker",
    "Smith", "Jones", "Taylor", "Brown", "Wilson",
    "Clark", "Walker", "Hall", "Green", "Adams",
]

# Company names - all clearly synthetic
_COMPANIES = [
    "Example Networks Ltd",
    "Example Mobility Ltd",
    "Sample Communications Ltd",
    "Demo Services Ltd",
    "Test Solutions Ltd",
    "Mock Enterprises Ltd",
    "Synthetic Corp Ltd",
    "Placeholder Holdings Ltd",
    "Sandbox Technologies Ltd",
    "Prototype Systems Ltd",
]

_BUSINESS_TYPES = ["SMB", "CORP", "GLOBAL"]
_EMPLOYEE_BANDS = ["0-9", "10-49", "50-99", "100-249", "250"]

# Synthetic UK-style postcodes
_POSTCODES = [
    "EX1 1AA", "EX2 2BB", "EX3 3CC", "EX4 4DD", "EX5 5EE",
    "TE1 1ST", "TE2 2ND", "TE3 3RD", "TE4 4TH", "TE5 5TH",
    "SA1 1MP", "SA2 2LE", "SA3 3AB", "SA4 4CD", "SA5 5EF",
    "MO1 1CK", "MO2 2CK", "MO3 3CK", "MO4 4CK", "MO5 5CK",
]

# Synthetic job titles
JOB_TITLES = [
    "Manager", "Director", "Engineer", "Analyst", "Consultant",
    "Coordinator", "Specialist", "Administrator", "Supervisor", "Lead",
]


def generate_lead_pool(rng: random.Random, size: int = 50) -> list[dict[str, str | int]]:
    """Create a deterministic pool of synthetic leads.

    Args:
        rng: Seeded Random instance for deterministic output.
        size: Number of leads to generate.

    Returns:
        List of lead dictionaries.
    """
    leads: list[dict[str, str | int]] = []
    base_lead_id = 800000

    for i in range(size):
        lead_id = base_lead_id + rng.randint(0, 99999)
        first_name = rng.choice(_FIRST_NAMES)
        last_name = rng.choice(_LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
        phone = f"+44-555-{rng.randint(100, 999):03d}{rng.randint(0, 9)}"
        company = rng.choice(_COMPANIES)
        business_type = rng.choice(_BUSINESS_TYPES)
        employee_band = rng.choice(_EMPLOYEE_BANDS)
        postal_code = rng.choice(_POSTCODES)

        leads.append({
            "leadId": lead_id,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "company": company,
            "businessType": business_type,
            "employeeBand": employee_band,
            "postalCode": postal_code,
        })

    return leads


def select_lead(rng: random.Random, pool: list[dict[str, str | int]]) -> dict[str, str | int]:
    """Select a random lead from the pool."""
    return rng.choice(pool)
