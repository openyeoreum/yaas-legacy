import sys
sys.path.append("/yaas")

from agent.a1_Api.a14_Models import Question, Answer
from datetime import datetime

q = Question(subject = 'pybo가 무엇인가요?', content = 'pybo에 대해서 알고싶습니다.', create_date = datetime.now())

from agent.a1_Api.a13_Database import SessionLocal
db = SessionLocal()
db.add(q)
db.commit()

q = Question(subject = 'FastAPI 모델 질문 입니다.', content = 'id는 자동으로 생성 되나요?', create_date = datetime.now())
db.add(q)
db.commit()

a = Answer(question = q, content = '네 자동으로 생성 됩니다.', create_date = datetime.now())
db.add(a)
db.commit()