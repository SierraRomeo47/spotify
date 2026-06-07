"""Tag formatting tests."""

from data_processing import format_tag_label


def test_format_tag_label_slashes():
    assert format_tag_label("electronic/uk") == "Electronic · UK"


def test_format_tag_label_hiphop():
    assert "Hip-Hop" in format_tag_label("punjabi hip-hop")
