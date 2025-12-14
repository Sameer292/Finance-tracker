from fastapi import FastAPI
from routes import authRoutes, transactions, categoryRoutes
from db.database import engine
import db.models
from middlewares.authMiddleWare import AuthMiddleware
from fastapi.security import HTTPBearer

app = FastAPI(
    title="Your API",
    description="This is my API",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(AuthMiddleware)
auth_scheme = HTTPBearer()

@app.on_event("startup")
async def startup():
    db.models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Working"}

app.include_router(authRoutes.router)
app.include_router(transactions.router)
app.include_router(categoryRoutes.router)
