from fastapi import APIRouter

from database.db import get_db

router = APIRouter(prefix="/api/menus", tags=["menus"])


@router.get("")
def list_menus():
    docs = list(get_db()["menus"].find({}, {"_id": 0}).sort("order", 1))
    panels: dict[str, list[dict]] = {}
    for doc in docs:
        panels.setdefault(doc.get("panel", ""), []).append(
            {
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),
                "order": doc.get("order", 0),
                "icon": bool(doc.get("icon", False)),
            }
        )
    return {"panels": [{"panel": name, "items": items} for name, items in panels.items()]}
