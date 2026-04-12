import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse


class CustomerService:

    def __init__(self, tenant_id: uuid.UUID):
        self.repo = CustomerRepository(tenant_id)

    async def create(self, db: AsyncSession, data: CustomerCreate) -> CustomerResponse:
        customer = await self.repo.create(db, data)
        return CustomerResponse.model_validate(customer)

    async def get_by_id(self, db: AsyncSession, customer_id: uuid.UUID) -> CustomerResponse:
        customer = await self.repo.get_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )
        return CustomerResponse.model_validate(customer)

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> dict:
        customers, total = await self.repo.get_all(db, skip, limit, search)
        return {
            "items": [CustomerResponse.model_validate(c) for c in customers],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        data: CustomerUpdate,
    ) -> CustomerResponse:
        customer = await self.repo.get_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )
        customer = await self.repo.update(db, customer, data)
        return CustomerResponse.model_validate(customer)

    async def delete(self, db: AsyncSession, customer_id: uuid.UUID) -> dict:
        customer = await self.repo.get_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )
        await self.repo.delete(db, customer)
        return {"message": "Cliente eliminado correctamente"}