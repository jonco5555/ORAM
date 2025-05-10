class Block:
    def __init__(self, data: str = "xxxx") -> None:
        self._data = data


class Bucket:
    def __init__(self, num_blocks: int = 4) -> None:
        self._blocks = [Block() for _ in range(num_blocks)]


class TreeNode[T]:
    def __init__(self, value: T) -> None:
        self.value: T = value
        self.left: TreeNode[T] = None
        self.right: TreeNode[T] = None


class Server:
    def __init__(self, tree_hight: int = 4) -> None:
        self._tree_hight = tree_hight
        self._root = self.initialize_tree(self._tree_hight)

    def initialize_tree(self, depth: int) -> TreeNode[Bucket]:
        if depth < 0:
            return None
        node = TreeNode(Bucket())
        node.left = self.initialize_tree(depth - 1)
        node.right = self.initialize_tree(depth - 1)
        return node

    def remap_block(self, position: int):
        pass

    def read_path(self, id: int):
        node = self._root
        path = [node]
        for level in range(self._tree_hight - 1, -1, -1):
            if (id >> level) & 1:
                path.append(node.right)
                node = node.right
            else:
                path.append(node.left)
                node = node.left
        return path
