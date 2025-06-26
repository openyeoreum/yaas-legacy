import sys
sys.path.append("/yaas")

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from agent.a1_Connector.a12_Database import GetDB
from agent.a1_Connector.domain.question import question_schema, question_crud

router = APIRouter(prefix = "/api/question")

@router.get("/list", response_model = list[question_schema.Question])
def question_list(db: Session = Depends(GetDB)):
    _question_list = question_crud.get_question_list(db)
    return _question_list

@router.get("/yaas")
def yaas_data():
    _yaas_data = question_crud.get_yaas()
    return _yaas_data