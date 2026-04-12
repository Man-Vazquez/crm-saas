import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerRepository(BaseRepository):

    async def create(self, db: AsyncSession, data: CustomerCreate) -> Customer:
        customer = Customer(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        db.add(customer)
        await db.flush()
        await db.refresh(customer)
        return customer

    async def get_by_id(self, db: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
        result = await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.tenant_id == self.tenant_id,
                Customer.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> tuple[list[Customer], int]:
        query = select(Customer).where(
            Customer.tenant_id == self.tenant_id,
            Customer.is_active == True,
        )

        if search:
            query = query.where(
                Customer.full_name.ilike(f"%{search}%")
            )

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total

    async def update(
        self,
        db: AsyncSession,
        customer: Customer,
        data: CustomerUpdate,
    ) -> Customer:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        await db.flush()
        await db.refresh(customer)
        return customer

    async def delete(self, db: AsyncSession, customer: Customer) -> Customer:
        customer.is_active = False
        await db.flush()
        return customer