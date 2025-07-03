import sys
sys.path.append("/yaas")

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.b2_Database import GetDB
from backend.b5_Domain.question.question_schema import QuestionSchema
from backend.b5_Domain.question.question_crud import GetQuestionList

question_router = APIRouter(prefix = "/api/question",)

@question_router.get("/list", response_model = list[QuestionSchema])
def qusetion_list(db: Session = Depends(GetDB)):
    _question_list = GetQuestionList(db)
    return _question_list