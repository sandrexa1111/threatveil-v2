from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..security import verify_jwt

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/rescan")
async def agent_rescan(token: str = Query(...)) -> dict:
    try:
        verify_jwt(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"ok": True}
