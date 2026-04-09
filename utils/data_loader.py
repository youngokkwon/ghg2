import json
from pathlib import Path
from typing import Any, Dict, List


def load_companies(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("companies", [])


def load_activity_by_company(path: Path, company_id: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f).get("data", [])
    return next((item for item in data if item.get("companyId") == company_id), {"companyId": company_id, "sections": {}})
