
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import ebooklib
from ebooklib import epub
from md2epub.epub_extractor import EpubExtractor

@pytest.fixture
def mock_epub_book():
    book = MagicMock(spec=epub.EpubBook)
    book.get_metadata.side_effect = lambda namespace, name: {
        ('DC', 'title'): [('Test Book', {})],
        ('DC', 'creator'): [('Test Author', {})],
        ('DC', 'language'): [('en', {})],
    }.get((namespace, name), None)
    
    book.spine = [('item1', 'yes'), ('item2', 'yes')]
    book.toc = []
    
    # Mock items
    item1 = MagicMock(spec=epub.EpubItem)
    item1.get_type.return_value = ebooklib.ITEM_DOCUMENT
    item1.file_name = 'chapter1.xhtml'
    item1.get_content.return_value = b'<html><body><h1>Chapter 1</h1><p>Test content.</p></body></html>'
    
    item2 = MagicMock(spec=epub.EpubItem)
    item2.get_type.return_value = ebooklib.ITEM_IMAGE
    item2.file_name = 'image.jpg'
    item2.get_content.return_value = b'fakeimage'

    book.get_item_with_id.side_effect = lambda x: item1 if x == 'item1' else item2 if x == 'item2' else None
    book.get_items.return_value = [item1, item2]
    
    return book

@patch('md2epub.epub_extractor.epub.read_epub')
def test_extract_metadata(mock_read_epub, mock_epub_book):
    mock_read_epub.return_value = mock_epub_book
    
    # We need a fake path that exists, or mock Path.exists
    with patch('pathlib.Path.exists', return_value=True):
        extractor = EpubExtractor('dummy.epub')
        extractor.extract_metadata()
        
        assert extractor.metadata['title'] == 'Test Book'
        assert extractor.metadata['author'] == 'Test Author'
        assert extractor.metadata['language'] == 'en'

def test_convert_html_to_md():
    # We can test this without mocking epub since it's a static method logical equivalent
    # But it's an instance method in our class
    with patch('md2epub.epub_extractor.epub.read_epub'), patch('pathlib.Path.exists', return_value=True):
        extractor = EpubExtractor('dummy.epub')
        html = '<html><head></head><body><h1>Title</h1><p>Text</p></body></html>'
        md = extractor.convert_html_to_md(html)
        assert '# Title' in md
        assert 'Text' in md
        assert '<html>' not in md

@patch('md2epub.epub_extractor.epub.read_epub')
def test_save_project(mock_read_epub, mock_epub_book, tmp_path):
    mock_read_epub.return_value = mock_epub_book
    
    with patch('pathlib.Path.exists', return_value=True):
        extractor = EpubExtractor('dummy.epub')
        extractor.extract_metadata()
        
        output_dir = tmp_path / "output"
        extractor.save_project(output_dir)
        
        assert output_dir.exists()
        assert (output_dir / "metadata.yaml").exists()
        assert (output_dir / "images").exists()
        assert (output_dir / "images" / "image.jpg").exists()
        
        # Check chapter file
        # The filename generation depends on title extraction.
        # Our mock content has header "Chapter 1", so title -> "Chapter 1" -> slug "chapter-1"
        # It's a chapter because it's not front matter
        # So filename: chapter_01_chapter-1.md
        expected_chapter = output_dir / "chapter_01_chapter-1.md"
        assert expected_chapter.exists()
        
        content = expected_chapter.read_text()
        assert "# Chapter 1" in content

def test_build_toc_map():
    # Test _build_toc_map logic with mocked TOC structure
    with patch('md2epub.epub_extractor.epub.read_epub') as mock_read:
        mock_book = MagicMock()
        # Create TOC structure: [Link(href='f1', title='T1'), [Link(href='f2', title='T2')]]
        l1 = MagicMock()
        l1.href = 'file1.xhtml'
        l1.title = 'Title 1'
        
        l2 = MagicMock()
        l2.href = 'file2.xhtml#anchor'
        l2.title = 'Title 2'
        
        mock_book.toc = [l1, [l2]]
        mock_read.return_value = mock_book
        
        with patch('pathlib.Path.exists', return_value=True):
            extractor = EpubExtractor('dummy.epub')
            mapping = extractor._build_toc_map()
            
            assert mapping.get('file1.xhtml') == 'Title 1'
            assert mapping.get('file2.xhtml') == 'Title 2'

def test_extract_chapter_title_heuristics(mock_epub_book, tmp_path):
    # Test title extraction when TOC map fails
    # 1. From Content (H1)
    # 2. Fallback to Chapter X
    
    with patch('md2epub.epub_extractor.epub.read_epub', return_value=mock_epub_book), \
         patch('pathlib.Path.exists', return_value=True):
        
        extractor = EpubExtractor('dummy.epub')
        # Clear TOC map to force heuristics
        extractor.href_to_title = {}
        
        # item1 has <h1>Chapter 1</h1>
        # item2 is image
        
        output_dir = tmp_path / "out_heuristic"
        extractor.save_project(output_dir)
        
        # Should produce chapter_01_chapter-1.md
        assert (output_dir / "chapter_01_chapter-1.md").exists()

def test_empty_content_handling(mock_epub_book, tmp_path):
    # Mock an empty item
    empty_item = MagicMock(spec=epub.EpubItem)
    empty_item.get_type.return_value = ebooklib.ITEM_DOCUMENT
    empty_item.file_name = 'empty.xhtml'
    empty_item.get_content.return_value = b''
    
    mock_epub_book.get_items.return_value.append(empty_item)
    # Add to spine
    mock_epub_book.spine.append(('empty_id', 'yes'))
    
    # Fix recursion: use a dict lookup or a dedicated function that doesn't call the mock method itself
    original_get_item = mock_epub_book.get_item_with_id.side_effect
    
    def get_item_side_effect(item_id):
        if item_id == 'empty_id':
            return empty_item
        # We know from the fixture that side_effect is a lambda that checks 'item1' and 'item2'
        # We can just replicate that logic or use the original if it was set, 
        # but original was a lambda attached to side_effect which might be tricky to call if it wasn't bound.
        # Let's just define the full logic here for simplicity since we know the fixture's items.
        # Retrieving the items from what we know they should be:
        # Fixture defined item1 and item2. We can't easily access them here unless we extract them from mock_epub_book.get_items()
        
        # Better: iterate get_items() return value matching IDs?
        # But get_items() returns a list.
        # Let's look at what items are available.
        items = mock_epub_book.get_items.return_value
        # item1 and item2 logic from fixture:
        # item1 -> 'item1', item2 -> 'item2'
        if item_id == 'item1':
            return items[0]
        if item_id == 'item2':
            return items[1]
        return None

    mock_epub_book.get_item_with_id.side_effect = get_item_side_effect
    
    with patch('md2epub.epub_extractor.epub.read_epub', return_value=mock_epub_book), \
         patch('pathlib.Path.exists', return_value=True):
         
        extractor = EpubExtractor('dummy.epub')
        output_dir = tmp_path / "out_empty"
        extractor.save_project(output_dir)
        
        # Verify empty file was skipped (as per logic added in previous steps)
        # We need to check if 'empty.md' or similar exists.
        # Since logic says "Check for empty content... continue", it should NOT exist.
        for f in output_dir.glob("*.md"):
             if "empty" in f.name:
                 assert False, "Empty file should not be created"
