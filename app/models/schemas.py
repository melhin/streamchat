from pydantic import BaseModel

class User(BaseModel):
    username: str
    active: bool = False
    class Config:
        orm_mode = True
