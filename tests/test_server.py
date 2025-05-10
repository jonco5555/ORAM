import pytest
from server import Server, TreeNode, Bucket


def generate_tree_hights():
    for h in range(6):
        for id in range(int(2 ** (h - 1))):
            yield h, id


@pytest.mark.parametrize("tree_hight, id", generate_tree_hights())
def test_read_path(tree_hight, id):
    if id >= 2 ** (tree_hight - 1):
        pytest.skip(
            f"Skipping id {id} as it is out of range for tree_hight {tree_hight}"
        )

    server = Server(tree_hight=tree_hight)
    path = server.read_path(id)

    # Validate the path contains the correct number of nodes
    assert len(path) == tree_hight + 1

    # Validate each node in the path is a TreeNode containing a Bucket
    for node in path:
        assert isinstance(node, TreeNode)
        assert isinstance(node.value, Bucket)
