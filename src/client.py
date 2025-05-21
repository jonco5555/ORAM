import logging
import math
import random
from typing import List

from cryptography.fernet import Fernet
from pydantic import BaseModel

from src.server import Server

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Block(BaseModel):
    id: int = -1
    data: str = "xxxx"


class Bucket(BaseModel):
    blocks: List[Block]

    def __init__(self, num_blocks: int = 4, blocks: List[Block] = None, **data) -> None:
        if blocks:
            super().__init__(blocks=blocks, **data)
        else:
            super().__init__(blocks=[Block() for _ in range(num_blocks)], **data)


class Client:
    def __init__(self, num_blocks: int = 100, blocks_per_bucket: int = 4) -> None:
        self._logger = logging.getLogger(__name__)
        self._num_blocks = num_blocks
        self._num_blocks_per_bucket = blocks_per_bucket
        self._tree_height = round(math.log2(num_blocks))
        self._stash: dict[int, Block] = {}  # Changed from List to dict
        self._position_map = {}
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)

    def _remap_block(self, block_id: int):
        new_position = random.randint(0, int(2**self._tree_height) - 1)
        self._position_map[block_id] = new_position
        self._logger.debug(f"Block {block_id} remapped to position {new_position}.")

    def store_data(self, server: Server, id: int, data: str):
        self._logger.info(f"Storing data for block {id}.")
        leaf_index = self._position_map.get(id)
        self._remap_block(id)
        if not leaf_index:  # if new block
            leaf_index = self._position_map.get(id)
        self._logger.debug(f"Leaf index for block {id}: {leaf_index}.")
        path = server.get_path(leaf_index)
        path = self._decrypt_and_parse_path(path)
        self._update_stash(path, id)

        # write new data to stash
        self._stash[id] = Block(id=id, data=data)
        self._logger.debug(f"Stash updated with block {id}.")

        path = self._build_new_path(leaf_index)
        path = self._unparse_and_encrypt_path(path)
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} stored successfully.")

    def retrieve_data(self, server: Server, id: int) -> str:
        self._logger.info(f"Retrieving data for block {id}.")
        leaf_index = self._position_map.get(id)
        if leaf_index is None:
            self._logger.warning(f"Block {id} not found.")
            return None
        self._remap_block(id)
        path = server.get_path(leaf_index)
        path = self._decrypt_and_parse_path(path)
        self._update_stash(path, id)
        block = self._stash.get(id)
        path = self._build_new_path(leaf_index)
        path = self._unparse_and_encrypt_path(path)
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} retrieved successfully.")
        return block.data

    def delete_data(self, server: Server, id: int) -> None:
        self._logger.info(f"Deleting data for block {id}.")
        leaf_index = self._position_map.get(id)
        if leaf_index is None:
            self._logger.warning(f"Block {id} not found.")
            return None
        path = server.get_path(leaf_index)
        path = self._decrypt_and_parse_path(path)
        self._update_stash(path, id)
        del self._stash[id]
        del self._position_map[id]
        self._logger.debug(f"Block {id} removed from stash.")
        path = self._build_new_path(leaf_index)
        path = self._unparse_and_encrypt_path(path)
        server.set_path(path, leaf_index)
        self._logger.info(f"Data for block {id} deleted successfully.")

    def _update_stash(self, path: List[Bucket], id: int) -> None:
        self._logger.debug(f"Updating stash with path for block {id}.")
        for bucket in path:
            for block in bucket.blocks:
                if block.id != -1:  # not a dummy block
                    self._stash[block.id] = block

    def _build_new_path(self, leaf_index: int) -> List[Bucket]:
        self._logger.debug(f"Building new path for leaf index {leaf_index}.")
        path = [
            Bucket(self._num_blocks_per_bucket) for _ in range(self._tree_height + 1)
        ]

        # Iterate over the tree levels from leaf to root
        for level in range(self._tree_height, -1, -1):
            reachable_leaves = self._calculate_reachable_leaves(leaf_index, level)
            bucket_index = self._tree_height - level
            num_written_blocks = 0
            block_ids = list(
                self._stash.keys()
            )  # to avoid modifying dict during iteration
            for block_id in block_ids:
                if num_written_blocks >= self._num_blocks_per_bucket:
                    break
                if self._position_map.get(block_id) in reachable_leaves:
                    path[bucket_index].blocks[num_written_blocks] = self._stash[
                        block_id
                    ]
                    del self._stash[block_id]
                    num_written_blocks += 1
        return path

    def _calculate_reachable_leaves(self, leaf_index: int, level: int) -> List[int]:
        binary = format(leaf_index, f"0{self._tree_height}b")
        # Get first level bits (path so far)
        path_bits = binary[:level]
        # Compute base index: decimal of path_bits * 2^(L-level)
        base = (
            int(path_bits, 2) * (1 << (self._tree_height - level)) if path_bits else 0
        )
        # Number of reachable leaves: 2^(L-level)
        num_leaves = 1 << (self._tree_height - level)
        # List of reachable leaves
        return list(range(base, base + num_leaves))

    def _decrypt_and_parse_path(self, path: List[List[bytes]]) -> List[Bucket]:
        new_path = []
        for bucket in path:
            blocks = [
                Block.model_validate_json(self._cipher.decrypt(data).decode())
                for data in bucket
            ]
            new_path.append(Bucket(blocks=blocks))
        return new_path

    def _unparse_and_encrypt_path(self, path: List[Bucket]) -> List[List[bytes]]:
        server_path = []
        for bucket in path:
            bucket_data = [
                self._cipher.encrypt(block.model_dump_json().encode())
                for block in bucket.blocks
            ]
            server_path.append(bucket_data)
        return server_path

    def _initialize_server_tree(self, server: Server) -> None:
        dummy_elements = [
            Bucket(self._num_blocks_per_bucket)
            for _ in range(int(2 ** (self._tree_height + 1) - 1))
        ]
        dummy_elements = self._unparse_and_encrypt_path(dummy_elements)
        server.initialize_tree(dummy_elements)

    def print_stash(self):
        """Prints the current contents of the stash."""
        self._logger.info("Printing stash contents:")
        if not self._stash:
            print("[]")
        else:
            for block_id, block in self._stash.items():
                print(f"Block ID: {block_id}, Data: {block.data}")
