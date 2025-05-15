from src.server import Server, Bucket
import pytest


@pytest.mark.parametrize("leaf_index", [0, 1, 2, 3])
@pytest.mark.parametrize("depth", [0, 1, 2, 3, 4])
@pytest.mark.parametrize("blocks_per_bucket", [3, 4, 5])
def test_get_path(depth, blocks_per_bucket, leaf_index):
    if leaf_index >= 2 ** (depth - 1):
        pytest.skip(f"Skipping test for leaf_index {leaf_index} at depth {depth}.")
    num_blocks = int(2 ** (depth + 1) - 1) * blocks_per_bucket
    server = Server(num_blocks=num_blocks, blocks_per_bucket=blocks_per_bucket)
    path = server.get_path(leaf_index)
    assert len(path) == depth + 1, f"Path length mismatch for leaf_index {leaf_index}"
    assert all(isinstance(bucket, Bucket) for bucket in path), (
        "Path contains non-Bucket elements"
    )
