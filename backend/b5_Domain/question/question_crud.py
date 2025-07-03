import sys
sys.path.append("/yaas")

from sqlalchemy.orm import Session
from backend.b3_Models import Question, Answer

def GetQuestionList(db: Session) -> list[Question]:
    question_list = db.query(Question).order_by(Question.create_date.desc()).all()
    return question_list