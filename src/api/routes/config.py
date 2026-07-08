from fastapi import APIRouter
from pydantic import BaseModel
from src.state.manager import StateManager

router = APIRouter(prefix="/api/config", tags=["config"])


class SaveKeyRequest(BaseModel):
    provider: str
    key: str


_state_mgr: StateManager | None = None


def init(state_mgr: StateManager):
    global _state_mgr
    _state_mgr = state_mgr


@router.post("/keys")
def save_api_key(body: SaveKeyRequest):
    _state_mgr.save_api_key(body.provider, body.key)
    return {"status": "ok"}


@router.get("/keys")
def list_api_keys():
    return _state_mgr.get_api_keys()


@router.delete("/keys/{provider}")
def delete_api_key(provider: str):
    _state_mgr.delete_api_key(provider)
    return {"status": "ok"}