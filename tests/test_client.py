from unittest.mock import patch

from src.client import Block, Bucket, Client
from src.server import Server


def test_retrieve_after_store_new_leaf_id():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    new_leaf_index = 1
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._initialize_server_tree(server)

    # Act
    with patch("random.randint", return_value=leaf_index):
        client.store_data(server, block_id, block_data)
    with patch("random.randint", return_value=new_leaf_index):
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert block_id in client._stash  # Stash should be empty after retrieval
    assert block_id in client._position_map


def test_retrieve_after_store_same_leaf_id():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    blocks_per_bucket = 2
    num_blocks = 14
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)  # L=2
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


def test_new_data_to_same_path_leaves_stash_empty():
    # Arrange
    server = Server(num_blocks=6, blocks_per_bucket=2)
    client = Client(num_blocks=6, blocks_per_bucket=2)

    with patch("random.randint", return_value=1):
        # Act
        client.store_data(server, 1, "abcd")
        client.store_data(server, 2, "efgh")

    # Assert
    assert not client._stash


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
