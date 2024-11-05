_scriptname = "Routers"

from fastapi import APIRouter
from starlette.responses import RedirectResponse
from OSUCS461.Routers.v1 import router as v1

router = APIRouter()
router.include_router(v1, prefix="/v1")


@router.get("/")
async def redirect_to_ap():
	return RedirectResponse(url="https://oregonstate.edu")
