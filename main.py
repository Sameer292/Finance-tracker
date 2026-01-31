from fastapi import FastAPI
from routes import authRoutes, transactionRoutes, categoryRoutes
from db.database import engine
import db.models as models
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager

auth_scheme = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Expensia",
    description="This is the finance tracker API for my Expensia app",
    version="1.0.2",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
    contact={
        "name": "Sameer paudel",
        "url": "http://github.com/sameer292",
        "email": "paudelsameer888@gmail.com",
    },
)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Working"}


app.include_router(authRoutes.router, tags=["Auth"])
app.include_router(transactionRoutes.router, tags=["Transactions"])
app.include_router(categoryRoutes.router, tags=["Categories"])
