import datetime
import sys
sys.path.append("/yaas")

from pydantic import BaseModel

class QuestionSchema(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime.datetime