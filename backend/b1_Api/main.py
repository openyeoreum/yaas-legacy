from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 - credentials와 * 동시 사용 불가
origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://0.0.0.0:5174",
    "http://172.18.0.4:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 또는 구체적인 origins 목록
    allow_credentials=True, # allow_origins=["*"]일 경우 False
    allow_methods=["*"],    # 모든 HTTP 메소드 허용 (OPTIONS 포함)
    allow_headers=["*"],    # 모든 헤더 허용
)

@app.get("/hello")
def hello():
    return {"message": " 안 녕 하 세 요 파 이 보 "}