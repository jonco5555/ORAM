from unittest.mock import patch

import pytest

from src.client import Block, Bucket, Client
from src.server import Server


@pytest.fixture
def server() -> Server:
    return Server()


@pytest.fixture
def client(server: Server) -> Client:
    c = Client()
    c._initialize_server_tree(server)
    return c


@pytest.fixture
def block_id() -> int:
    return 1


@pytest.fixture
def block_data() -> str:
    return "data"


def test_store_data(client: Client, server: Server, block_id: int, block_data: str):
    # Arrange
    leaf_index = 0

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)

    # Assert
    assert not client._stash  # block should be in root
    path = client._decrypt_and_parse_path(server.get_path(leaf_index))
    assert path[-1].blocks[0].data == block_data
    assert client._position_map.get(block_id) == leaf_index


def test_retrieve_after_store_new_leaf_id(
    client: Client, server: Server, block_id: int, block_data: str
):
    # Arrange
    leaf_index = 0
    new_leaf_index = 2**client._tree_height - 1

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)
    with patch("random.randint", return_value=new_leaf_index):
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert not client._stash  # block should be in root
    print(client._decrypt_and_parse_path(server.get_path(leaf_index)))
    assert (
        client._decrypt_and_parse_path([server._root._value.blocks])[0].blocks[0].data
        == block_data
    )
    assert client._position_map.get(block_id) == new_leaf_index


def test_retrieve_after_store_same_leaf_id(
    client: Client, server: Server, block_id: int, block_data: str
):
    # Arrange
    leaf_index = 0

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert not client._stash  # Stash should be empty after retrieval
    assert block_id in client._position_map


def test_encryption(block_id: int, block_data: str):
    # Arrange
    client = Client(num_blocks=6, blocks_per_bucket=2)
    path = [
        Bucket(blocks=[Block(id=block_id, data=block_data), Block()]),
        Bucket(2),
        Bucket(2),
        Bucket(2),
    ]

    # Act
    encrypted_path = client._unparse_and_encrypt_path(path)
    decrypted_path = client._decrypt_and_parse_path(encrypted_path)

    # Assert
    assert decrypted_path[0].blocks[0].id == block_id
    assert decrypted_path[0].blocks[0].data == block_data


def test_delete(client: Client, server: Server, block_id: int, block_data: str):
    # Act
    client.store_data(server, block_id, block_data)
    client.delete_data(server, block_id)

    # Assert
    assert not client._stash  # Stash should be empty after retrieval
    assert not client._position_map


def test_retrieve_not_found(client: Client, server: Server, block_id: int):
    # Act
    result = client.retrieve_data(server, block_id)

    # Assert
    assert result is None  # Should return None if block is not found


def test_flow(client: Client, server: Server, block_id: int, block_data: str):
    # Act & Assert
    client.store_data(server, block_id, block_data)
    assert client.retrieve_data(server, block_id) == block_data

    client.store_data(server, 2, block_data)
    client.delete_data(server, block_id)
    assert not client.retrieve_data(server, block_id)
    assert client.retrieve_data(server, 2) == block_data
    assert client.retrieve_data(server, 2) == block_data


def test_smart_stash_retrieval(
    client: Client, server: Server, block_id: int, block_data: str
):
    # Act
    with patch("random.randint", return_value=0):
        client.store_data(server, block_id, block_data)
    with patch("random.randint", return_value=1):
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert not client._stash
    # During the path building in the client side, we take elements from the stash
    # even though the block is now mapped to leaf 1, and we build path for lead 0,
    # there are nodes in the path that are mutual for both paths to leaves 0 and 1.
    # Therefor, when we reach to a node where the path to any of the leaves in the stash
    # goes through, we can take the block from the stash and add it to the path,
    # and not just the block that is mapped to the same leaf we build the path for.
    # For the leftest leaf and the rightest leaf, the mutual node is the root,
    # which is in any path
    # This test should pass.


def test_reachable_leaves():
    # Arrange
    client = Client(num_blocks=8)

    leaf_index = 5
    reachable_leaves = [[0, 1, 2, 3, 4, 5, 6, 7], [4, 5, 6, 7], [4, 5], [5]]
    # Act & Assert
    for i in range(4):
        assert reachable_leaves[i] == client._calculate_reachable_leaves(leaf_index, i)
