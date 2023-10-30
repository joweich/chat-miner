import sys
import pytest


def test_visualization_import():
    try:
        from chatminer import visualizations
        assert "visualizations" in sys.modules
    except ImportError as e:
        pytest.fail(f"Error importing visualizations: {e}")
