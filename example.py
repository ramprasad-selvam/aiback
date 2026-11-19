import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from claims_agent import evaluate_claim

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("claims.example")


def load_dotenv(path: Path) -> None:
  if not path.exists():
    return
  for raw_line in path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, value = line.split("=", 1)
    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(Path(__file__).with_name(".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

TEST_CASES: dict[str, dict[str, Any]] = {
    "clean": {
        "raw_document_text": """
        Claim ID: CLM-2026-002
        Patient Name: Alice Smith
        Patient ID: PT-1002
        Provider Name: Metro General Hospital
        Provider NPI: 9876543210
        Date of Service: 2026-11-15
        Diagnosis: ICD-10 J06.9
        Line Item: Office visit - $140.00
        Line Item: X-ray - $70.00
        Total Claimed Amount: $210.00
        """,
        "policy_details": {
            "coverage_tier": "gold",
            "deductible_limit": 500,
            "exclusions": ["cosmetic surgery"],
            "covered_diagnosis_codes": ["J06.9"],
            "line_item_allowable_thresholds": {
                "office visit": 200,
                "x-ray": 100,
            },
            "standard_regional_rates": {"office visit": 150, "x-ray": 75},
        },
        "historical_claims": [],
    },
    "duplicate": {
        "raw_document_text": """
        Claim ID: CLM-2026-001
        Patient Name: John Doe
        Patient ID: PT-1001
        Provider Name: Northside Clinic
        Provider NPI: 1234567890
        Date of Service: 2026-11-18
        Diagnosis: ICD-10 J06.9
        Line Item: Office visit - $150.00
        Line Item: X-ray - $75.00
        Total Claimed Amount: $225.00
        """,
        "policy_details": {
            "coverage_tier": "gold",
            "deductible_limit": 500,
            "exclusions": ["cosmetic surgery"],
            "covered_diagnosis_codes": ["J06.9"],
            "line_item_allowable_thresholds": {
                "office visit": 200,
                "x-ray": 100,
            },
            "standard_regional_rates": {"office visit": 150, "x-ray": 75},
        },
        "historical_claims": [{
            "claim_id": "CLM-2026-001",
            "patient_id": "PT-1001",
            "date_of_service": "2026-11-18",
            "total_claimed_amount": 225.00,
            "status": "PAID",
        }],
    },
    "fraud_mismatch": {
        "raw_document_text": """
        Claim ID: CLM-2026-003
        Patient Name: Robert Johnson
        Patient ID: PT-1003
        Provider Name: Elite Aesthetics Center
        Provider NPI: 5556667771
        Date of Service: 2026-11-16
        Diagnosis: ICD-10 Z41.1
        Line Item: Cosmetic rhinoplasty consultation and procedure - $4500.00
        Total Claimed Amount: $4500.00
        """,
        "policy_details": {
            "coverage_tier": "silver",
            "deductible_limit": 1000,
            "exclusions": ["cosmetic surgery"],
            "covered_diagnosis_codes": ["J06.9", "E11.9"],
            "line_item_allowable_thresholds": {"consultation": 150},
            "standard_regional_rates": {"consultation": 100},
        },
        "historical_claims": [],
    },
    "missing_fields": {
        "raw_document_text": """
        Claim ID: CLM-2026-004
        Patient Name: Emily Davis
        Provider Name: City Health Care
        Date of Service: 2026-11-17
        Diagnosis: ICD-10 E11.9
        Line Item: Diabetes routine checkup - $300.00
        Total Claimed Amount: $300.00
        """,
        "policy_details": {
            "coverage_tier": "gold",
            "deductible_limit": 500,
            "exclusions": ["cosmetic surgery"],
            "covered_diagnosis_codes": ["E11.9"],
            "line_item_allowable_thresholds": {"diabetes routine checkup": 250},
            "standard_regional_rates": {"diabetes routine checkup": 200},
        },
        "historical_claims": [],
    },
}


def build_payload(case_name: str) -> dict[str, Any]:
  base = TEST_CASES[case_name]
  return {
      **base,
      "groq_api_key": GROQ_API_KEY,
      "groq_model": GROQ_MODEL,
  }


def run_case(case_name: str) -> None:
  logger.info("Starting claims evaluation for case=%s", case_name)
  result = evaluate_claim(build_payload(case_name))
  logger.info("Claims evaluation completed for case=%s", case_name)
  print(f"=== CASE: {case_name} ===")
  print(json.dumps(result, indent=2))


def main() -> None:
  if GROQ_API_KEY:
    logger.info("Groq enabled: model=%s", GROQ_MODEL)
  else:
    logger.warning(
        "Groq not enabled: set GROQ_API_KEY in the environment or .env"
    )

  requested = sys.argv[1] if len(sys.argv) > 1 else "clean"

  if requested == "all":
    for name in TEST_CASES:
      run_case(name)
  elif requested in TEST_CASES:
    run_case(requested)
  else:
    available = ", ".join([*TEST_CASES.keys(), "all"])
    raise SystemExit(
        f"Unknown case '{requested}'. Choose one of: {available}"
    )


if __name__ == "__main__":
  main()