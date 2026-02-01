import pytest
import os
from unittest.mock import MagicMock, patch
from md2epub.story_creation.agents import (
    narrative_architect_agent,
    character_designer_agent,
    mythologist_agent,
    chapter_outliner_agent,
    editor_agent,
    editor_critique_agent,
    world_builder_agent,
    logistics_manager_agent,
    EditorDecision,
    init_llm
)

@pytest.fixture(autouse=True)
def mock_env():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy"}):
        yield

@pytest.fixture
def mock_llm_response():
    with patch("md2epub.story_creation.agents.init_llm") as mock_init:
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Mock Content"
        mock_llm.invoke.return_value = mock_response
        mock_init.return_value = mock_llm
        yield mock_llm, mock_response

@patch("md2epub.story_creation.agents.write_markdown_file")
def test_all_sequential_agents(mock_write, mock_llm_response):
    """Test all standard sequential agents to ensure they call the LLM and write files."""
    mock_llm, mock_response = mock_llm_response
    state = {"user_output_dir": "test_out"}
    
    # List of agents to test
    agents = [
        (mythologist_agent, "hero_journey", "hero-journey.md"),
        (chapter_outliner_agent, "chapters", "chapters.md"),
        (editor_agent, "author_notes", "author-notes.md"),
        (world_builder_agent, "lore", "lore.md"),
        (logistics_manager_agent, "plot_items", "plot-items.md")
    ]
    
    for agent_func, state_key, filename in agents:
        result = agent_func(state)
        assert result[state_key] == "Mock Content"
        mock_write.assert_any_call(filename, "Mock Content", "test_out")

@patch("md2epub.story_creation.agents.init_llm")
@patch("md2epub.story_creation.agents.write_markdown_file")
def test_agent_refinement_logic(mock_write, mock_init_llm):
    """Test that agents incorporate critique feedback into their prompts."""
    mock_llm = MagicMock()
    mock_init_llm.return_value = mock_llm
    
    # Test Narrative Architect
    state_na = {"premise": "P", "genre": "G", "critique": "Darker.", "user_output_dir": "test_out"}
    narrative_architect_agent(state_na)
    assert "Darker." in mock_llm.invoke.call_args[0][0][1].content
    
    # Test Character Designer
    state_cd = {"save_the_cat": "Outline", "critique": "More robots.", "user_output_dir": "test_out"}
    character_designer_agent(state_cd)
    assert "More robots." in mock_llm.invoke.call_args[0][0][1].content

@patch("md2epub.story_creation.agents.init_llm")
def test_editor_critique_paths(mock_init_llm):
    """Test both APPROVE and REVISE paths of the editor critique agent."""
    mock_llm = MagicMock()
    mock_init_llm.return_value = mock_llm
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    
    # Path 1: REVISE
    mock_structured.invoke.return_value = EditorDecision(action="REVISE", critique="Too happy.")
    res_revise = editor_critique_agent({"iteration": 0}, {"configurable": {"max_iterations": 1}})
    assert res_revise["critique"] == "Too happy."
    
    # Path 2: APPROVE
    mock_structured.invoke.return_value = EditorDecision(action="APPROVE")
    res_approve = editor_critique_agent({"iteration": 0}, {"configurable": {"max_iterations": 1}})
    assert res_approve["critique"] is None

def test_editor_critique_max_iterations():
    """Test that the editor approves automatically when max iterations are reached."""
    state = {"iteration": 2}
    config = {"configurable": {"max_iterations": 2}}
    result = editor_critique_agent(state, config)
    assert result["critique"] is None

@patch("md2epub.story_creation.agents.ChatOpenAI")
def test_init_llm_params(mock_chat):
    """Test the LLM factory with custom parameters."""
    params = {"model_name": "gpt-mini", "temperature": 0.1}
    init_llm(params)
    mock_chat.assert_called_with(model="gpt-mini", temperature=0.1, base_url=None)
