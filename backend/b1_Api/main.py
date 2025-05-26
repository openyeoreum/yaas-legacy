from fastapi import FastAPI, Request
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

@app.get("/yaas")
def hello(request: Request):
    # IP 확인용
    client_ip = request.client.host if request.client else "unknown"
    origin = request.headers.get("origin", "no-origin")
    print(f"Request from IP: {client_ip}")
    print(f"Origin: {origin}")
    return {"message": "Hello, YaaS!", "your_ip": client_ip, "origin": origin}