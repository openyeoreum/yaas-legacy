import sys
sys.path.append("/yaas")

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from agent.a1_Api.a16_Routers import UserRouter
from agent.a1_Api.domain.question.question_router import router as QuestionRouter

app = FastAPI(debug = True)

# CORS 설정 - credentials와 * 동시 사용 불가
origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://0.0.0.0:5174",
    "http://172.18.0.4:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins, # 또는 구체적인 origins 목록
    allow_credentials = True, # allow_origins=["*"]일 경우 False
    allow_methods = ["*"],    # 모든 HTTP 메소드 허용 (OPTIONS 포함)
    allow_headers = ["*"],    # 모든 헤더 허용
)

#### 학습 후 삭제 ####
app.include_router(QuestionRouter)
#### 학습 후 삭제 ####

app.include_router(UserRouter)
# app.include_router(a1112_UserHistoryRouter.router)
# app.include_router(a1113_SubscriptionRouter.router)
# app.include_router(a1114_SubscriptionHistoryRouter.router)
# app.include_router(a1115_ProjectsStorageRouter.router)
# app.include_router(a1116_ProjectsStorageHistoryRouter.router)
# app.include_router(a1116_ProjectsRouter.router)
# app.include_router(a1118_ProjectHistoryRouter.router)