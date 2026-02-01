from pydantic import BaseModel
from schemas.TransactionSchemas import Transaction


class Category(BaseModel):
    name: str
    color: str
    icon: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str
    icon: str


class AllCategories(BaseModel):
    categories: list[CategoryResponse]


class CategoryTransactionResponse(BaseModel):
    category_id: int
    transactions: list[Transaction]


class AddCategoryResponse(BaseModel):
    id: int
    message: str


class DeleteAllCategoriesResponse(BaseModel):
    message: str
