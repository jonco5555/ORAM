from unittest.mock import patch

from src.client import Block, Bucket, Client
from src.server import Server


def test_store_data():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    blocks_per_bucket = 2
    num_blocks = 14  # L=2
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)

    # Assert
    assert not client._stash  # block should be in root
    path = client._decrypt_and_parse_path(server.get_path(leaf_index))
    assert path[-1].blocks[0].data == block_data
    assert client._position_map.get(block_id) == leaf_index


def test_retrieve_after_store_new_leaf_id():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    new_leaf_index = 3
    blocks_per_bucket = 2
    num_blocks = 14  # L=2
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

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


def test_retrieve_after_store_same_leaf_id():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    blocks_per_bucket = 2
    num_blocks = 14  # L=2
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert not client._stash  # Stash should be empty after retrieval
    assert block_id in client._position_map


def test_encryption():
    # Arrange
    client = Client(num_blocks=6, blocks_per_bucket=2)
    path = [
        Bucket(blocks=[Block(id=1, data="abcd"), Block()]),
        Bucket(2),
    ]

    # Act
    encrypted_path = client._unparse_and_encrypt_path(path)
    decrypted_path = client._decrypt_and_parse_path(encrypted_path)

    # Assert
    assert decrypted_path[0].blocks[0].id == 1
    assert decrypted_path[0].blocks[0].data == "abcd"


def test_delete():
    # Arrange
    block_id = 1
    block_data = "data"
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act
    client.store_data(server, block_id, block_data)
    client.delete_data(server, block_id)

    # Assert
    assert not client._stash  # Stash should be empty after retrieval
    assert not client._position_map


def test_retrieve_not_found():
    # Arrange
    block_id = 1
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act
    result = client.retrieve_data(server, block_id)

    # Assert
    assert result is None  # Should return None if block is not found


def test_flow():
    # Arrange
    block_id = 1
    block_data = "data"
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act & Assert
    client.store_data(server, block_id, block_data)
    assert client.retrieve_data(server, block_id) == block_data

    client.store_data(server, 2, block_data)
    client.delete_data(server, block_id)
    assert not client.retrieve_data(server, block_id)
    assert client.retrieve_data(server, 2) == block_data
    assert client.retrieve_data(server, 2) == block_data


def test_smart_stash_retrieval():
    # Arrange
    block_id = 1
    block_data = "data"
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

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
    blocks_per_bucket = 2
    num_blocks = 30  # L = 3
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)

    leaf_index = 5
    reachable_leaves = [[0, 1, 2, 3, 4, 5, 6, 7], [4, 5, 6, 7], [4, 5], [5]]
    # Act & Assert
    for i in range(4):
        assert reachable_leaves[i] == client._calculate_reachable_leaves(leaf_index, i)
