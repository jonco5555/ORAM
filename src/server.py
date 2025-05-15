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
from collections import deque

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Block:
    def __init__(self, id: int = -1, data: str = "xxxx") -> None:
        self._id = id
        self._data = data

    def __str__(self) -> str:
        """
        Returns a string representation of the block, showing its ID and data.
        """
        return f"({self._id},{self._data})"

    # def __repr__(self) -> str:
    #     """
    #     Returns a string representation of the block, showing its ID and data.
    #     """
    #     return self.__str__()


class Bucket:
    def __init__(self, num_blocks: int = 4) -> None:
        self._blocks = [Block() for _ in range(num_blocks)]

    def __str__(self) -> str:
        """
        Returns a string representation of the bucket, showing the IDs of the blocks.
        """
        return f"[{', '.join(str(block) for block in self._blocks)}]"

    # def __repr__(self) -> str:
    #     """
    #     Returns a string representation of the block, showing its ID and data.
    #     """
    #     return self.__str__()


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
        self._root = self.initialize_tree(self._tree_height)

    def initialize_tree(self, depth: int) -> TreeNode[Bucket]:
        if depth < 0:
            return None
        node = TreeNode(Bucket(self._blocks_per_bucket))
        node._left = self.initialize_tree(depth - 1)
        node._right = self.initialize_tree(depth - 1)
        return node

    def get_path(self, leaf_index: int) -> List[Bucket]:
        """
        Retrieve the path from the root of the tree to the specified leaf.

        This method runs through the tree from the root to the leaf and collects the
        buckets. The path is determined by the binary representation of `leaf_index`,
        where each bit indicates whether to move to the left (0) or right (1) child
        at each level of the tree.

        Args:
            leaf_index (int): The index of the leaf node to retrieve the path for

        Returns:
            List[Bucket]: A list of `Bucket` objects representing the values of
              the nodes along the path from the root to the specified leaf

        Raises:
            ValueError: If the `leaf_index` is out of bounds for the tree height
        """
        if leaf_index < 0 or leaf_index >= 2**self._tree_height:
            raise ValueError(
                f"Leaf index {leaf_index} is out of bounds for tree height {self._tree_height}"
            )
        self._logger.debug(f"Retrieving path for leaf index {leaf_index}")
        node = self._root
        path = [node._value]
        for level in range(self._tree_height - 1, -1, -1):
            if (leaf_index >> level) & 1:
                path.append(node._right._value)
                node = node._right
            else:
                path.append(node._left._value)
                node = node._left
        return path

    def set_path(self, path: List[Bucket], leaf_index: int) -> None:
        """
        Write the specified path to the tree on the path to the leaf

        This method runs through the tree from the root to the leaf, and writes the
        provided path of `Bucket` objects to the corresponding nodes in the tree.

        Args:
            path (List[Bucket]): The list of `Bucket` objects to write to the tree
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
        self._root._value = path.pop()
        for level in range(self._tree_height - 1, -1, -1):
            if (leaf_index >> level) & 1:
                node._right._value = path.pop()
                node = node._right
            else:
                node._left._value = path.pop()
                node = node._left

    def print_tree(self) -> None:
        """
        Print the tree in a structured and readable format.

        This method performs a level-order traversal of the tree and prints
        each level on a new line, showing the structure of the tree.
        """
        if not self._root:
            print("Tree is empty.")
            return

        queue = deque([(self._root, 0)])  # Queue to hold nodes and their levels
        current_level = 0
        level_nodes = []

        while queue:
            node, level = queue.popleft()

            # If we move to a new level, print the collected nodes of the previous level
            if level != current_level:
                print(
                    f"Level {current_level}: {' '.join(str(n._value) for n in level_nodes)}"
                )
                level_nodes = []
                current_level = level

            level_nodes.append(node)

            # Add child nodes to the queue
            if node._left:
                queue.append((node._left, level + 1))
            if node._right:
                queue.append((node._right, level + 1))

        # Print the last level
        if level_nodes:
            print(
                f"Level {current_level}: {' '.join(str(n._value) for n in level_nodes)}"
            )
