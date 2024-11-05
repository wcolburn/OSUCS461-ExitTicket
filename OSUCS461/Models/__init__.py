from pydantic import BaseModel

class BasePydanticModel(BaseModel):
	class Config:
		from_attributes = False
		validate_assignment = True
