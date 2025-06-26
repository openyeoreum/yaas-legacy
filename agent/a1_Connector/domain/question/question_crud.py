import json
import sys
sys.path.append("/yaas")

from agent.a1_Connector.a14_Models import Question, Answer
from sqlalchemy.orm import Session

def get_question_list(db: Session):
    question_list = db.query(Question).order_by(Question.create_date.desc()).all()
    return question_list

def get_yaas():
    with open('/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/250527_꼭알아야할생명과학샘플/250527_꼭알아야할생명과학샘플_audiobook/250527_꼭알아야할생명과학샘플_master_audiobook_file/[250527_꼭알아야할생명과학샘플_AudioBook_Edit].json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data