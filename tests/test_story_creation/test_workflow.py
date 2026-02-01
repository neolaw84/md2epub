import pytest
from md2epub.story_creation.workflow import create_story_graph

def test_create_story_graph():
    app = create_story_graph()
    assert app is not None
    # Verify nodes exist
    nodes = app.nodes
    assert "NarrativeArchitect" in nodes
    assert "CharacterDesigner" in nodes
    assert "WorldBuilder" in nodes
    assert "LogisticsManager" in nodes
