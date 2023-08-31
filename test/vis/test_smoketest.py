import pytest


def test_visualization_import():
    try:
        import chatminer.visualizations as vis
    except ImportError as e:
        pytest.fail(f"Error importing visualizations: {e}")
