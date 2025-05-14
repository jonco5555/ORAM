import math
import random
from typing import List
from server import Block, Bucket, Server


class Client:
    def __init__(self, num_blocks: int = 124, blocks_per_bucket: int = 4) -> None:
        self._num_blocks = num_blocks
        self._num_blocks_per_bucket = blocks_per_bucket
        self._tree_height = math.log2(num_blocks // blocks_per_bucket + 1) - 1
        self._stash: List[Block] = []
        self._position_map = {}

    def remap_block(self, block_id: int):
        new_position = random.randint(0, 2**self._tree_height - 1)
        self._position_map[block_id] = new_position

    def store_data(self, server: Server, id: int, data: str):
        pass

    def retrieve_data(self, server: Server, id: int):
        leaf_index = self._position_map.get(id)
        if leaf_index is None:
            return None
        self.remap_block(id)
        path = server.get_path(leaf_index)

        # add the blocks in the path to the stash
        for bucket in path:
            for block in bucket._blocks:
                if block._id != -1:  # not a dummy block
                    self._stash.append(block)

        # write to path all the blocks in the stash that are mapped to the same leaf
        # and remove the from the stash
        new_path = [Bucket() for _ in path]
        blocks_to_remove = []
        bucket_index = 0
        block_index = 0
        for block in self._stash:
            if self._position_map.get(block._id) == leaf_index:
                new_path[bucket_index]._blocks[block_index] = block
                blocks_to_remove.append(block)
                block_index += 1
                if block_index == self._num_blocks_per_bucket:  # full bucket
                    bucket_index += 1
                    block_index = 0

        # remove the blocks from the stash
        for block in blocks_to_remove:
            self._stash.remove(block)

        server.write_path(new_path)

        # return the desired block
        for block in self._stash:
            if block._id == id:
                return block._data

    def delete_data(self, server: Server, id: int, data: str):
        pass
