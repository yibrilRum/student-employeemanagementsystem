from motor.motor_asyncio import AsyncIOMotorCollection

async def create_indexes(
    users_collection: AsyncIOMotorCollection,
    employees_collection: AsyncIOMotorCollection
):
    # Users: unique username
    await users_collection.create_index("username", unique=True)

    # Employees: unique employeeId
    await employees_collection.create_index("employeeId", unique=True)