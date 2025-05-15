from unittest.mock import MagicMock, patch
from src.client import Client
from src.server import Server, Block, Bucket


def test_retrieve_data_existing_block():
    # Arrange
    block_id = 1
    block_data = "data"
    leaf_index = 0
    new_leaf_index = 1
    blocks_per_bucket = 2
    num_blocks = 14
    bucket = Bucket(blocks_per_bucket)
    block = Block(block_id, block_data)
    bucket._blocks[0] = block

    server = Server(num_blocks=14, blocks_per_bucket=blocks_per_bucket)  # L=2
    server.get_path = MagicMock(
        return_value=[Bucket(blocks_per_bucket), Bucket(blocks_per_bucket), bucket]
    )
    server.set_path = MagicMock()
    client = Client(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    client._position_map[block_id] = leaf_index

    with patch("random.randint", return_value=new_leaf_index):
        # Act
        result = client.retrieve_data(server, block_id)

    # Assert
    assert result == block_data
    assert client._stash[block_id]._data == block._data
    assert client._position_map[block_id] == new_leaf_index
    server.get_path.assert_called_once_with(leaf_index)
    path, index = server.set_path.call_args[0]
    for bucket in path:
        assert bucket._blocks[0]._id == -1
    assert index == leaf_index
