import pytest
from casare_rpa.infrastructure.cache.keys import CacheKeyGenerator


def test_deterministic_hashing_order_insensitivity():
    """Verify that dictionary key order does not affect the hash."""
    gen = CacheKeyGenerator()

    data1 = {"a": 1, "b": 2, "c": {"x": 10, "y": 20}}
    data2 = {"c": {"y": 20, "x": 10}, "b": 2, "a": 1}

    key1 = gen.generate("test_node", data1)
    key2 = gen.generate("test_node", data2)

    assert key1 == key2
    assert isinstance(key1, str)
    assert len(key1) > 20  # Format: namespace:version:hash16


def test_different_node_types_different_keys():
    """Verify that different node types with same data produce different keys."""
    gen = CacheKeyGenerator()
    data = {"input": "value"}

    key1 = gen.generate("node_a", data)
    key2 = gen.generate("node_b", data)

    assert key1 != key2


def test_nested_structures():
    """Verify complex nested structures are hashed correctly."""
    gen = CacheKeyGenerator()
    data = {
        "list": [1, 2, {"nested": "dict"}],
        "bool": True,
        "none": None,
        "float": 1.5,
    }

    key = gen.generate("complex_node", data)
    assert key is not None


def test_namespace_isolation():
    """Verify that namespaces prevent collisions."""
    gen = CacheKeyGenerator()
    data = {"id": 123}

    key_node = gen.generate("my_node", data)
    key_api = gen.generate("api", data)

    assert key_node != key_api
    assert "api:" in key_api
