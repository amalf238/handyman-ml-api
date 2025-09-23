import os, json, logging, requests
from typing import Tuple, Dict, Any, List

def setup_logging():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    return logging.getLogger("utils")

# ------- dataset helpers -------
def load_json_dataset(path_or_url: str):
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        r = requests.get(path_or_url, timeout=30)
        if r.status_code != 200:
            raise Exception(f"Failed to download dataset: {r.status_code}")
        return r.json()
    with open(path_or_url, "r", encoding="utf-8") as f:
        return json.load(f)

def get_github_dataset_url(user: str, repo: str, file_path: str, branch: str="main"):
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"

# ------- validation / formatting you already used -------
def validate_query(data: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Invalid JSON"
    if "query" not in data:
        return False, "Missing 'query'"
    if not str(data["query"]).strip():
        return False, "Query cannot be empty"
    return True, ""

def create_error_response(message: str) -> Dict[str, Any]:
    return {"success": False, "error": message}

def create_success_response(workers: List[Dict[str, Any]], query: str, metadata: Dict[str, Any]):
    return {"success": True, "query": query, "workers": workers, "metadata": metadata}

def format_worker_response(worker: Dict[str, Any], score: float, distance: float, confidence: float):
    return {
        "id": worker.get("id"),
        "name": worker.get("worker_name") or worker.get("name"),
        "service": worker.get("service_category") or worker.get("service_type"),
        "rating": worker.get("rating"),
        "pricePerHour": worker.get("price_per_hour") or worker.get("pricing", {}).get("daily_wage_lkr"),
        "city": (worker.get("location") or {}).get("city") or worker.get("city"),
        "imageUrl": worker.get("imageUrl"),
        "score": round(float(score), 4),
        "distance_km": round(float(distance), 2),
        "confidence": round(float(confidence) * 100, 1),
    }
