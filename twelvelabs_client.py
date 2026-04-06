import time
from twelvelabs import TwelveLabs

API_KEY = "tlk_21Z5MBN2YMWJM02ZJP6A70NTEKEP"
INDEX_NAME = "compliance-demo-v4"

client = TwelveLabs(api_key=API_KEY)


def create_index():
    print("Creating or fetching index...")

    indexes = list(client.indexes.list())

    for idx in indexes:
        if idx.index_name == INDEX_NAME:
            print(f"Found existing index: {idx.index_name}")
            return idx.id

    print("Creating new index...")

    index = client.indexes.create(
        index_name=INDEX_NAME,
        models=[
            {
                "model_name": "marengo3.0",
                "model_options": ["visual", "audio"]
            },
            {
                "model_name": "pegasus1.2",
                "model_options": ["visual", "audio"]
            }
        ]
    )

    print("Created index:", index.id)
    return index.id


def upload_video(index_id, video_path):
    import os
    import time

    print("Uploading video...")
    print("File exists:", os.path.exists(video_path))

    with open(video_path, "rb") as f:
        task = client.tasks.create(
            index_id=index_id,
            video_file=f
        )

    print("Task ID:", task.id)
    print("Entering polling loop...")

    while True:
        print("Checking task status...")

        try:
            task_status = client.tasks.retrieve(task.id)

            print("Status:", task_status.status)

            if task_status.status == "ready":
                print("Video indexed")
                print("Video ID:", task_status.video_id)
                return task_status.video_id

            elif task_status.status == "failed":
                print("FAILED TASK:", task_status)
                raise Exception("Indexing failed")

        except Exception as e:
            print("Error retrieving task:", e)

        time.sleep(3)


def run_compliance_query(index_id, video_id):
    queries = {
        "profanity": "strong profanity, swearing, explicit offensive language",
        "drugs": "drug use or illegal behavior",
        "alcohol": "alcohol consumption or drinking",
        "unsafe_usage": "unsafe or incorrect makeup usage",
        "misleading_claims": "misleading cosmetic or medical claims",
        "hate": "hate speech or harassment"
    }

    results = {}

    for category, q in queries.items():
        print(f"\nRunning query for: {category}")

        response = client.search.query(
            index_id=index_id,
            query_text=q,
            search_options=["visual", "audio"]
        )

        results[category] = response

    return results
    
def filter_by_video(results, target_video_id):
    filtered = {}

    for category, response in results.items():
        filtered_items = []

        for item in list(response):
            if item["video_id"] == target_video_id:
                filtered_items.append(item)

        filtered[category] = filtered_items

    return filtered
    
def extract_violations(filtered_results):
    violations = []

    KEYWORDS = {
        "profanity": ["damn", "shit", "fuck"],
        "drugs": ["drug", "cocaine", "weed"],
        "alcohol": ["drink", "wine", "beer"],
        "unsafe_usage": ["danger", "unsafe"],
        "misleading_claims": ["guaranteed", "instant"],
        "hate": ["hate", "idiot", "stupid"]
    }

    for category, items in filtered_results.items():
        for item in items:
            text = item["transcription"].lower()
            item["start"]

            # filter: only keep if keyword actually matches
            if not any(word in text for word in KEYWORDS.get(category, [])):
                continue

            violations.append({
                "category": category,
                "severity": "medium",
                "timestamps": [seconds_to_mmss(item.start)],
                "explanation": item.transcription
            })

    return violations
    
def seconds_to_mmss(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"
    
def build_compliance(violations):
    if not violations:
        return {
            "overall_status": "clear",
            "decision": "APPROVE",
            "issues": []
        }

    return {
        "overall_status": "flagged",
        "decision": "REVIEW",
        "issues": violations
    }

def deduplicate_violations(violations):
    seen = set()
    unique = []

    for v in violations:
        key = (v["category"], tuple(v["timestamps"]))

        if key not in seen:
            seen.add(key)
            unique.append(v)

    return unique
    
def assign_severity(text):
    text = text.lower()

    if any(w in text for w in ["fuck", "shit"]):
        return "high"

    if any(w in text for w in ["damn"]):
        return "medium"

    return "low"

    return {
        "overall_status": "flagged",
        "issues": violations
    }
import json


def analyze_video(prompt, video_id):
    response = client.analyze(
        video_id=video_id,
        prompt=prompt
    )
    return response
def run_compliance_query(index_id, video_id):
    import time
    import json

    queries = {
        "profanity": "strong profanity, swearing, explicit offensive language",
        "drugs": "drug use or illegal behavior",
        "alcohol": "alcohol consumption or drinking",
        "unsafe_usage": "unsafe or incorrect makeup usage",
        "misleading_claims": "misleading cosmetic or medical claims",
        "hate": "hate speech or harassment"
    }

    results = {}

    for category, q in queries.items():
        print(f"\nRunning query for: {category}")

        response = client.search.query(
            index_id=index_id,
            query_text=q,
            search_options=["visual", "audio"]
        )

        results[category] = [
            {
                "video_id": item.video_id,
                "start": item.start,
                "end": item.end,
                "transcription": item.transcription
            }
            for item in list(response)
        ]

        time.sleep(2)

        with open("cached_results.json", "w") as f:
            json.dump(results, f, indent=2)

    return results
    
