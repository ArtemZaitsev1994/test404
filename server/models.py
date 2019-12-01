from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


COLLECTION = 'User'


class User:

    def __init__(self, db: AsyncIOMotorDatabase, name: str):
        self.db = db
        self.collection = self.db[COLLECTION]
        self.name = name

    async def check_user(self) -> Dict[str, str]:
        """Проверка существования юзера"""
        return await self.collection.find_one({'name': self.name})

    async def get_contacts(self) -> List[Dict]:
        """Получить всех пользователей в системе"""
        user = await self.collection.find_one({'name': self.name})
        if user is not None:
            return user['contacts']
        return None

    async def add_contact(self, contact: Dict[str, str]) -> bool:
        """
        Добавить контакт к пользователю

        Args:
            contact - данные с идентификаторами в мессенджерах
        """
        result = await self.collection.find_one_and_update(
            {'name': self.name},
            {'$set': {f'contacts.{contact["name"]}': contact['messangers']}}
        )
        return result

    async def remove_contact(self, contact_name: str):
        """Удалить контакт из списка контактов"""
        result = await self.collection.find_one_and_update(
            {'name': self.name},
            {'$unset': {f'contacts.{contact_name}': ''}}
        )
        return result

    async def create_user(self):
        """Создание пользователя на основе экземпляра класса"""
        user = await self.check_user()
        if not user:
            result = await self.collection.insert_one({
                'name': self.name,
                'contacts': {},
            })

    async def clear_db(self):
        await self.collection.drop()
