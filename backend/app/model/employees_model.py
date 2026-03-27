from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

async def add_employee(collection: AsyncIOMotorCollection, employee_data: dict):
    try:
        await collection.insert_one(employee_data)
        return await collection.find_one({"employeeId": employee_data["employeeId"]}, {"_id": 0})
    except DuplicateKeyError:
        raise DuplicateKeyError("Employee ID already exists")

async def get_all_employees(collection: AsyncIOMotorCollection, skip=0, limit=100):
    cursor = collection.find({}, {"_id": 0}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

async def get_employee_by_id(collection: AsyncIOMotorCollection, employee_id: str):
    return await collection.find_one({"employeeId": employee_id}, {"_id": 0})

async def get_employees_by_department(collection: AsyncIOMotorCollection, department: str):
    cursor = collection.find({"department": department}, {"_id": 0})
    return await cursor.to_list(length=100)

async def update_employee(collection: AsyncIOMotorCollection, employee_id: str, update_data: dict):
    return await collection.find_one_and_update(
        {"employeeId": employee_id},
        {"$set": update_data},
        return_document=True,
        projection={"_id": 0}
    )

async def delete_employee(collection: AsyncIOMotorCollection, employee_id: str):
    result = await collection.delete_one({"employeeId": employee_id})
    return result.deleted_count > 0