from pydantic import BaseModel
from typing import Any

class UserSchema(BaseModel):
    Email: str
    UserName: str
    ProfileImagePath: str
    
    class Config:
        from_attributes = Any
        
# class ProjectsStorageSchema(BaseModel):
#     ProjectsStorageID: int
#     ProjectsStorageDate: datetime.datetime
#     ProjectsStorageName: str
#     ProjectsStoragePath: str
    
#     class Config:
#         from_attributes = True
        
class ProjectsProcessSchema(BaseModel):
    Process: int
    
    class Config:
        from_attributes = True