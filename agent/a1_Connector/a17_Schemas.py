from pydantic import BaseModel
from typing import Any

class UserSchema(BaseModel):
    Email: str
    UserName: str
    ProfileImagePath: str
    
    class Config:
        from_attributes = True
        
class ProjectsStorageSchema(BaseModel):
    ProjectsStorageId: int
    ProjectsStorageName: str
    ProjectsStoragePath: str
    
    class Config:
        from_attributes = True
        
class ProjectsProcessSchema(BaseModel):
    Process: Any
    
    class Config:
        from_attributes = True