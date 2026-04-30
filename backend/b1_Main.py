import sys
sys.path.append("/yaas")

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.b5_Domain.b56_AudioBook.audiobook_router import audiobook_router

try:
    from backend.routers import UserRouter
    from backend.b5_Domain.question.question_router import question_router
except ModuleNotFoundError:
    UserRouter = None
    question_router = None

app = FastAPI(debug = True)

# CORS 설정 - credentials와 * 동시 사용 불가
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:15174",
    "http://127.0.0.1:15174",
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

@app.get("/hello")
def hello():
    return {"message": "사랑해요. 아공이!"}

if UserRouter is not None:
    app.include_router(UserRouter)
if question_router is not None:
    app.include_router(question_router)
app.include_router(audiobook_router)
# app.include_router(a1112_UserHistoryRouter.router)
# app.include_router(a1113_SubscriptionRouter.router)
# app.include_router(a1114_SubscriptionHistoryRouter.router)
# app.include_router(a1115_ProjectsStorageRouter.router)
# app.include_router(a1116_ProjectsStorageHistoryRouter.router)
# app.include_router(a1116_ProjectsRouter.router)
# app.include_router(a1118_ProjectHistoryRouter.router)
