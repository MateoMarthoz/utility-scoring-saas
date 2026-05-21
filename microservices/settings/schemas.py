def individual_serial(score) -> dict:
    return {
        "id": str(score["_id"]),
        "username": score["username"],
        "scenario": score["scenario"],
        "score": score["score"]
    }

def list_serial(scores) -> list:
    return[individual_serial(score) for score in scores]