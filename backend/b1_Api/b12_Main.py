import sys
sys.path.append("/yaas")

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.b1_Api.b16_Routers import UserRouter

app = FastAPI(debug=True)

origins = [
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(UserRouter)
# app.include_router(b1112_UserHistoryRouter.router)
# app.include_router(b1113_SubscriptionRouter.router)
# app.include_router(b1114_SubscriptionHistoryRouter.router)
app.include_router(b1115_ProjectsStorageRouter.router)
# app.include_router(b1116_ProjectsStorageHistoryRouter.router)
app.include_router(b1116_ProjectsRouter.router)
# app.include_router(b1118_ProjectHistoryRouter.router)