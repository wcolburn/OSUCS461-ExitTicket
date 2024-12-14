from pydantic import BaseModel
from datetime import datetime

class BasePydanticModel(BaseModel):
	class Config:
		from_attributes = False
		validate_assignment = True

class UserWrite(BaseModel):
	email: str

class User(UserWrite):
	uuid: int
	time_created: datetime
	last_seen: datetime

class UserPostWrite(BaseModel):
	post_9char: str
	text: str
	user_uuid: int

class UserPost(UserPostWrite):
	uuid: int
	time_created: datetime
