from typing import List
from server import Server

from pydantic import BaseModel


class FilePosition(BaseModel):
    name: str
    id: int


class Client:
    def __init__(self) -> None:
        self._stash = []
        self._position_map: List[FilePosition] = []

    def store_data(self, server: Server, id: int, data: str):
        pass

    def retrieve_data(self, server: Server, id: int):
        pass

    def delete_data(self, server: Server, id: int, data: str):
        pass
