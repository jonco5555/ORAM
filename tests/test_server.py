import pytest
from server import Server, TreeNode, Bucket


def generate_tree_heights():
    for h in range(6):
        for id in range(int(2 ** (h - 1))):
            yield h, id


@pytest.mark.parametrize("tree_height, id", generate_tree_heights())
def test_read_path(tree_height, id):
    if id >= 2 ** (tree_height - 1):
        pytest.skip(
            f"Skipping id {id} as it is out of range for tree_height {tree_height}"
        )

    server = Server(tree_height=tree_height)
    path = server.read_path(id)

    # Validate the path contains the correct number of nodes
    assert len(path) == tree_height + 1

    # Validate each node in the path is a TreeNode containing a Bucket
    for node in path:
        assert isinstance(node, TreeNode)
        assert isinstance(node._value, Bucket)
