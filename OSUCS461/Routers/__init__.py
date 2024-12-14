from http.client import HTTPException

_scriptname = "Routers"

from fastapi import APIRouter
from starlette.responses import RedirectResponse
from OSUCS461.Routers.v1 import router as v1
from OSUCS461.Classes.Database import DB
from OSUCS461.Classes.User import UserClass
from OSUCS461.Models import User, UserPost
from datetime import datetime

# Resource used for code below: https://www.youtube.com/watch?v=ID9b4diFZN8

router = APIRouter()
router.include_router(v1, prefix="/v1")

tables = DB.GetTables()
user_table = tables[0]

user_class = UserClass()

users_list = [
	# {"uuid": 1, "name": "user1", "time_created": datetime(2024, 12, 10, 0, 0, 0, 0), "last_seen": datetime(2024, 12, 10, 0, 0, 0, 0)},
	# {"uuid": 2, "name": "user2", "time_created": datetime(2024, 12, 10, 0, 0, 0, 0), "last_seen": datetime(2024, 12, 10, 0, 0, 0, 0)}
	{"uuid": 1, "email": "user1@gmail.com" },
	{"uuid": 2, "email": "user2@gmail.com" }
]

@router.get("/")
async def redirect_to_ap():
	return RedirectResponse(url="https://oregonstate.edu")

@router.get("/users")
async def get_users() -> list[User]:
	print("Hey!")
	tables = DB.GetTables()
	print(tables, flush=True)
	return [
		User(**u) for u in users_list
	]

@router.get("/users/{uuid}")
async def user_by_uuid(uuid: int) -> User:
	user = next((User(**u) for u in users_list if u['uuid'] == uuid), None)
	if user is None:
		raise HTTPException(status_code=404, detail="Invalid User ID")
	return user

@router.post("/users")
async def create_user(user_data: UserPost) -> User:
	return user_class.add_to_db(user_data)