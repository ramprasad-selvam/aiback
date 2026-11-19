# Health Insurance Claims Processing Agent

A LangGraph-based Python pipeline that validates health insurance claim state and returns strict JSON.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python example.py
pytest -q
```

## Input

```python
{
  "raw_document_text": str,
  "policy_details": dict,
  "historical_claims": list[dict]
}
```

The graph runs extraction, duplicate checking, coverage validation, fraud/anomaly detection, and missing-document detection in sequence.

Set `GROQ_API_KEY` or pass `groq_api_key` in the input to enable optional Groq-assisted extraction. Missing values remain null or empty rather than invented.

The public `evaluate_claim()` result uses the strict enterprise schema with claim identity, processing status, extracted data, triggered flags, missing documents, and auditor notes.
