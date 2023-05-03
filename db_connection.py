import high_score
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


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

    def get_highest_score(self, username) -> high_score.HighScore:
        docs = list(self._schema["users"].find(self._get_user_filter(username)))
        return self._to_high_score(rank=None, item=docs[0]) if len(docs) > 0 else None

    def get_highest_scores(self, limit: int) -> list:
        docs = list(
            self._schema["users"]
            .find()
            .sort("highest_score", pymongo.DESCENDING)
            .limit(limit)
        )

        return [
            self._to_high_score(rank=i + 1, item=item) for i, item in enumerate(docs)
        ]

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

    def _to_high_score(self, rank, item):
        return high_score.HighScore(
            rank=rank, name=item["name"], score=int(item["highest_score"])
        )
