# Z Number of blocks in a bucket
# L Number of levels in the tree
# N Number of blocks in the tree
# N / Z Total number of buckets
# L = log(N / Z + 1) - 1
# N = Z * (2 ** (L + 1) - 1)
# 2 ** L Number of leaves =  (N / Z) / 2


import logging
import math
from typing import List

from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Bucket(BaseModel):
    blocks: List[bytes]


class TreeNode[T]:
    def __init__(self, value: T) -> None:
        self._value: T = value
        self._left: TreeNode[T] = None
        self._right: TreeNode[T] = None


class Server:
    def __init__(self, num_blocks: int = 124, blocks_per_bucket: int = 4) -> None:
        self._logger = logging.getLogger(__name__)
        self._num_blocks = num_blocks
        self._blocks_per_bucket = blocks_per_bucket
        self._tree_height = int(math.log2(num_blocks // blocks_per_bucket + 1)) - 1
        self._root: TreeNode[Bucket] = None

    def initialize_tree(self, elements: List[List[bytes]]) -> TreeNode[Bucket]:
        def recursive_init(level: int, i: int) -> TreeNode[Bucket]:
            if level < 0:
                return None
            node = TreeNode(Bucket(blocks=elements[i]))
            node._left = recursive_init(level - 1, i + 1)
            node._right = recursive_init(level - 1, i + 2)
            return node

        self._root = recursive_init(self._tree_height, 0)

    def get_path(self, leaf_index: int) -> List[List[bytes]]:
        """
        Retrieve the path from the root of the tree to the specified leaf.

        This method runs through the tree from the root to the leaf and collects the
        buckets. The path is determined by the binary representation of `leaf_index`,
        where each bit indicates whether to move to the left (0) or right (1) child
        at each level of the tree.

        Args:
            leaf_index (int): The index of the leaf node to retrieve the path for

        Returns:
            List[List[str]]: A list of buckets represented as list of bytes, representing
              the values of the nodes along the path from the root to the specified leaf

        Raises:
            ValueError: If the `leaf_index` is out of bounds for the tree height
        """
        if leaf_index < 0 or leaf_index >= 2**self._tree_height:
            raise ValueError(
                f"Leaf index {leaf_index} is out of bounds for tree height {self._tree_height}"
            )
        self._logger.debug(f"Retrieving path for leaf index {leaf_index}")
        node = self._root
        path = [node._value.blocks]
        for level in range(self._tree_height - 1, -1, -1):
            if (leaf_index >> level) & 1:
                path.append(node._right._value.blocks)
                node = node._right
            else:
                path.append(node._left._value.blocks)
                node = node._left
        return path

    def set_path(self, path: List[List[bytes]], leaf_index: int) -> None:
        """
        Write the specified path to the tree on the path to the leaf

        This method runs through the tree from the root to the leaf, and writes the
        provided path of `Bucket` objects to the corresponding nodes in the tree.

        Args:
            path (List[List[bytes]]): The list of buckets to write to the tree
            leaf_index (int): The index of the leaf to write the path for

        Raises:
            ValueError: If the `leaf_index` is out of bounds for the tree height
        """
        if leaf_index < 0 or leaf_index >= 2**self._tree_height:
            raise ValueError(
                f"Leaf index {leaf_index} is out of bounds for tree height {self._tree_height}"
            )
        self._logger.debug(f"Writing path for leaf index {leaf_index}")
        node = self._root
        self._root._value.blocks = path.pop()
        for level in range(self._tree_height - 1, -1, -1):
            if (leaf_index >> level) & 1:
                node._right._value.blocks = path.pop()
                node = node._right
            else:
                node._left._value.blocks = path.pop()
                node = node._left
