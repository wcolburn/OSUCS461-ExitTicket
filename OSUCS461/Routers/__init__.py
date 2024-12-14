from http.client import HTTPException

_scriptname = "Routers"

from fastapi import APIRouter
from starlette.responses import RedirectResponse
from Routers.v1 import router as v1
from Classes.Database import DB
from Classes.User import UserClass
from Models import User, UserWrite
from datetime import datetime

# Resource used for code below: https://www.youtube.com/watch?v=ID9b4diFZN8

router = APIRouter()
router.include_router(v1, prefix="/v1")

tables = DB.GetTables()
user_table = tables[0]

user_class = UserClass()

@router.get("/")
async def redirect_to_ap():
	return RedirectResponse(url="https://oregonstate.edu")

@router.get("/users")
async def get_users() -> list[User]:
	return [
		User(**u) for u in user_class.get_users()
	]

@router.get("/users/{uuid}")
async def user_by_uuid(uuid: int) -> User:
	return user_class.get_user(uuid)

@router.post("/users")
async def create_user(user_data: UserWrite) -> User:
	return user_class.add_to_db(user_data)

@router.put("/users/{uuid}")
async def update_user(uuid: int, user_data: UserWrite) -> User:
	return user_class.update_user(uuid, user_data)