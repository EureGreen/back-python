from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from app import models
from app.database import get_db
from app.dependencies import PermissionChecker, get_current_user

router = APIRouter(prefix="/api", tags=["resources"])

# Mock данные для бизнес-объектов
MOCK_PRODUCTS = [
    {"id": 1, "name": "Product 1", "price": 100},
    {"id": 2, "name": "Product 2", "price": 200},
    {"id": 3, "name": "Product 3", "price": 300},
]

MOCK_ORDERS = [
    {"id": 1, "user_id": 1, "product_id": 1, "quantity": 2},
    {"id": 2, "user_id": 2, "product_id": 2, "quantity": 1},
]

@router.get("/products")
def get_products(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка аутентификации
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Проверка прав на чтение товаров
    permission_checker = PermissionChecker(["products:read"])
    try:
        permission_checker(current_user, db)
        return MOCK_PRODUCTS
    except HTTPException as e:
        if e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to products"
            )
        raise

@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Проверка прав
    permission_checker = PermissionChecker(["products:read"])
    try:
        permission_checker(current_user, db)
        
        product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product
    except HTTPException as e:
        if e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        raise

@router.post("/products")
def create_product(
    product: Dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Проверка прав на создание товаров
    permission_checker = PermissionChecker(["products:create"])
    try:
        permission_checker(current_user, db)
        
        # Mock создание товара
        new_product = {
            "id": len(MOCK_PRODUCTS) + 1,
            **product
        }
        MOCK_PRODUCTS.append(new_product)
        return new_product
    except HTTPException as e:
        if e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        raise

@router.get("/orders")
def get_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Проверка прав
    permission_checker = PermissionChecker(["orders:read"])
    try:
        permission_checker(current_user, db)
        
        # Фильтрация заказов для обычных пользователей
        if not current_user.is_superuser:
            user_orders = [o for o in MOCK_ORDERS if o["user_id"] == current_user.id]
            return user_orders
        return MOCK_ORDERS
    except HTTPException as e:
        if e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        raise