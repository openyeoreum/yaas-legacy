import datetime

from pydantic import BaseModel

class User(BaseModel):
    UserId: int
    UserDate: datetime.datetime
    Email: str
    _password: str
    UserName: str
    UserPath: str
    
    class Config:
        from_attributes = True