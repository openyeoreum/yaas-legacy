import datetime

from pydantic import BaseModel

class ProjectsStorage(BaseModel):
    ProjectsStorageID: int
    ProjectsStorageDate: datetime.datetime
    ProjectsStorageName: str
    ProjectsStoragePath: str
    
    class Config:
        from_attributes = True