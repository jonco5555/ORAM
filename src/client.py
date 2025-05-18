import math
import random
import logging
from typing import List

from pydantic import BaseModel
from src.server import Bucket, Server
from cryptography.fernet import Fernet

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Block(BaseModel):
    id: int = -1
    data: str = "xxxx"


class Client:
    def __init__(self, num_blocks: int = 124, blocks_per_bucket: int = 4) -> None:
        self._logger = logging.getLogger(__name__)
        self._num_blocks = num_blocks
        self._num_blocks_per_bucket = blocks_per_bucket
        self._tree_height = int(math.log2(num_blocks // blocks_per_bucket + 1)) - 1
        self._stash: dict[int, Block] = {}  # Changed from List to dict
        self._position_map = {}
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)

    def remap_block(self, block_id: int):
        new_position = random.randint(0, int(2**self._tree_height) - 1)
        self._position_map[block_id] = new_position
        self._logger.debug(f"Block {block_id} remapped to position {new_position}.")

    def store_data(self, server: Server, id: int, data: str):
        self._logger.info(f"Storing data for block {id}.")
        leaf_index = self._position_map.get(id)
        self.remap_block(id)
        if not leaf_index:  # if new block
            leaf_index = self._position_map.get(id)
        self._logger.debug(f"Leaf index for block {id}: {leaf_index}.")
        path = server.get_path(leaf_index)
        self._decrypt_and_parse_path(path)
        self._update_stash(path, id)

        # write new data to stash
        self._stash[id] = Block(id=id, data=data)
        self._logger.debug(f"Stash updated with block {id}.")

        path = self._build_new_path(leaf_index, len(path))
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} stored successfully.")

    def retrieve_data(self, server: Server, id: int) -> str:
        self._logger.info(f"Retrieving data for block {id}.")
        leaf_index = self._position_map.get(id)
        if leaf_index is None:
            self._logger.warning(f"Block {id} not found.")
            return None
        self.remap_block(id)
        path = server.get_path(leaf_index)
        self._decrypt_and_parse_path(path)
        self._update_stash(path, id)
        path = self._build_new_path(leaf_index, len(path))
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} retrieved successfully.")
        return self._stash.get(id).data

    def delete_data(self, server: Server, id: int) -> None:
        self._logger.info(f"Deleting data for block {id}.")
        leaf_index = self._position_map.get(id)
        if leaf_index is None:
            self._logger.warning(f"Block {id} not found.")
            return None
        path = server.get_path(leaf_index)
        self._decrypt_and_parse_path(path)
        self._update_stash(path, id)
        del self._stash[id]
        self._logger.debug(f"Block {id} removed from stash.")
        path = self._build_new_path(leaf_index, len(path))
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} deleted successfully.")

    def _update_stash(self, path: List[Bucket], id: int) -> None:
        self._logger.debug(f"Updating stash with path for block {id}.")
        for bucket in path:
            for block in bucket.blocks:
                if block.id != -1:  # not a dummy block
                    self._stash[block.id] = block

    def _build_new_path(self, leaf_index: int, path_length: int) -> List[Bucket]:
        self._logger.debug(f"Building new path for leaf index {leaf_index}.")
        path = [Bucket(self._num_blocks_per_bucket) for _ in range(path_length)]
        bucket_index = 0
        block_index = 0
        for block in list(self._stash.values()):
            if self._position_map.get(block.id) == leaf_index:
                path[bucket_index].blocks[block_index] = self._cipher.encrypt(
                    block.model_dump_json().encode()
                )
                del self._stash[block.id]
                block_index += 1
                if block_index == self._num_blocks_per_bucket:  # full bucket
                    bucket_index += 1
                    block_index = 0
        return path

    def _decrypt_and_parse_path(self, path: List[Bucket]) -> None:
        for bucket in path:
            for i, block in enumerate(bucket.blocks):
                bucket.blocks[i] = Block.model_validate_json(
                    self._cipher.decrypt(block).decode()
                )

    def _unparse_and_encrypt_path(self, path: List[Bucket]) -> None:
        for bucket in path:
            for i, block in enumerate(bucket.blocks):
                bucket.blocks[i] = self._cipher.encrypt(
                    block.model_dump_json().encode()
                )

    def print_stash(self):
        """Prints the current contents of the stash."""
        self._logger.info("Printing stash contents:")
        if not self._stash:
            print("[]")
        else:
            for block_id, block in self._stash.items():
                print(f"Block ID: {block_id}, Data: {block.data}")


if __name__ == "__main__":
    server = Server(num_blocks=14, blocks_per_bucket=2)
    server.print_tree()
    client = Client(num_blocks=14, blocks_per_bucket=2)
    client.store_data(server, 1, "abcd")
    server.print_tree()
    print(client._stash)
    client.store_data(server, 2, "efgh")
    server.print_tree()
    print(client._stash)
    print(client.retrieve_data(server, 2))
    server.print_tree()
    print(client._stash)
    client.delete_data(server, 2)
    server.print_tree()
    print(client._stash)
