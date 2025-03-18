from fastapi import FastAPI
from app.routes.video import router as video_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(video_router, prefix="/api")
app.include_router(user_router, prefix="/api/users")
app.include_router(auth_router, prefix="/api/auth")
