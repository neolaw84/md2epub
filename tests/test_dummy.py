import pytest
import md2epub
from md2epub import cli
from unittest.mock import patch

def test_module_import():
    """Test that the package can be imported."""
    assert md2epub is not None

def test_cli_main(capsys):
    """Test the CLI main function prints the expected output."""
    cli.main()
    captured = capsys.readouterr()
    assert "md2epub CLI" in captured.out

def test_cli_entry_point():
    """Test the __main__ block (simulation)."""
    # This is a bit tricky to test the actual if __name__ == "__main__": block 
    # without running it as a script, but we can verify the main function exists.
    assert callable(cli.main)
