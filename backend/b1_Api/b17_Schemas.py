from pydantic import BaseModel

class UserSchema(BaseModel):
    Email: str
    UserName: str
    ProfileImagePath: str
    
    class Config:
        from_attributes = True
        
# class ProjectsStorageSchema(BaseModel):
#     ProjectsStorageID: int
#     ProjectsStorageDate: datetime.datetime
#     ProjectsStorageName: str
#     ProjectsStoragePath: str
    
#     class Config:
#         from_attributes = True
        
# class ProjectsSchema(BaseModel):
#     UserId: int
#     UserDate: datetime.datetime
#     Email: str
#     _password: str
#     UserName: str
#     UserPath: str
    
#     class Config:
#         from_attributes = True