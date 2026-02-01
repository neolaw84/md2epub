import os
import shutil
import pytest
from md2epub.story_creation.tools import write_markdown_file, read_markdown_file

def test_write_markdown_file(tmp_path):
    output_dir = str(tmp_path / "test_output")
    filename = "test.md"
    content = "Hello World"
    
    # write_markdown_file adds 'story-elements' to the path if not present
    path = write_markdown_file(filename, content, output_dir)
    
    final_dir = os.path.join(output_dir, "story-elements")
    filepath = os.path.join(final_dir, filename)
    
    assert os.path.exists(filepath)
    with open(filepath, "r") as f:
        assert f.read() == content

def test_read_markdown_file(tmp_path):
    output_dir = str(tmp_path)
    filename = "test_read.md"
    content = "Read Me"
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.read = lambda: content # mock read for simpler test logic if needed, but let's just write/read
        f.write(content)
        
    read_content = read_markdown_file(filename, output_dir)
    assert read_content == content

def test_read_markdown_file_not_found():
    result = read_markdown_file("non_existent.md", "nowhere")
    assert "not found" in result.lower()
