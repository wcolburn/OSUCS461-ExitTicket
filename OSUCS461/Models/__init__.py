from pydantic import BaseModel
from datetime import datetime

class BasePydanticModel(BaseModel):
	class Config:
		from_attributes = False
		validate_assignment = True

class UserPost(BaseModel):
	uuid: int
	email: str

class User(UserPost):
	time_created: datetime
	last_seen: datetime
