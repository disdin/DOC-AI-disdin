from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None


mongo_db = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB."""
    mongo_db.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongo_db.db = mongo_db.client[settings.MONGO_DB_NAME]
    print(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    if mongo_db.client:
        mongo_db.client.close()
        print("MongoDB connection closed")
