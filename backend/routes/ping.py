from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/ping")
async def ping():
    return {"ok": True}
