import pytest


def test_visualization_import():
    try:
        import chatminer.visualizations as vis

        assert hasattr(vis, "sunburst")
        assert hasattr(vis, "wordcloud")
        assert hasattr(vis, "calendar_heatmap")
        assert hasattr(vis, "radar")
    except ImportError as e:
        pytest.fail(f"Error importing visualizations: {e}")
