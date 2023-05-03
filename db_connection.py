import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class HighestScore:
    def __init__(self, name: str, highest_score: int) -> None:
        self.name = name
        self.highest_score = highest_score

    def __str__(self) -> str:
        return '{{ "name": "{}", "highest_score": {} }}'.format(
            self.name, self.highest_score
        )

    def __repr__(self) -> str:
        return str(self)


class DbConnection:
    def __init__(self, connection_string: str) -> None:
        client = MongoClient(connection_string, server_api=ServerApi("1"))

        try:
            client.admin.command("ping")
            print("Successfully connected to MongoDB!")
            self._schema = client["snake"]
        except Exception as e:
            print(e)
            self._schema = None

    def is_connected(self) -> bool:
        return self._schema is not None

    def get_highest_score(self, username) -> HighestScore:
        docs = list(self._schema["users"].find(self._get_user_filter(username)))
        return self._to_highest_score(docs[0]) if len(docs) > 0 else None

    def get_highest_scores(self, limit: int) -> list:
        docs = list(
            self._schema["users"]
            .find()
            .sort("highest_score", pymongo.DESCENDING)
            .limit(limit)
        )

        return list(map(lambda item: self._to_highest_score(item), docs))

    def create_user(self, username) -> None:
        self._schema["users"].update_one(
            self._get_user_filter(username),
            {"$setOnInsert": {"highest_score": 0}},
            upsert=True,
        )

    def update_highest_score(self, username, score) -> None:
        self._schema["users"].update_one(
            self._get_user_filter(username), {"$max": {"highest_score": score}}
        )

    def _get_user_filter(self, username):
        return {"name": username}

    def _to_highest_score(self, item):
        return HighestScore(item["name"], int(item["highest_score"]))
