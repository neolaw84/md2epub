
import os
import shutil
import yaml
import re
from pathlib import Path
from ebooklib import epub
import ebooklib
from markdownify import markdownify as md
from bs4 import BeautifulSoup
from slugify import slugify # We might not have python-slugify installed? 
# cookiecutter depends on python-slugify? Yes, pyproject says so.
# checking pyproject: "cookiecutter" depends on "python-slugify>=4.0.0" so it should be there.
# But let's check imports. cookiecutter uses 'slugify' from 'python-slugify' package usually.
# Actually 'cookiecutter' depends on 'binaryornot', 'Jinja2', 'click', 'pyyaml'.
# python-slugify is often a transitive dep.
# Let's use a simple slugify function if not sure or check local environment.

def simple_slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

class EpubExtractor:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {self.epub_path}")
        self.book = epub.read_epub(self.epub_path)
        self.metadata = {}
        self.chapters = []
        self.front_matter = []
        self.href_to_title = self._build_toc_map()

    def _build_toc_map(self):
        """Builds a mapping from href to title using the TOC."""
        mapping = {}
        def traverse(items):
            for item in items:
                if isinstance(item, tuple) or isinstance(item, list):
                     traverse(item)
                elif hasattr(item, 'href') and hasattr(item, 'title'):
                    # href might include anchors like 'chapter.xhtml#section'
                    # We want just the filename part for matching spine items?
                    # But spine items have unique hrefs usually.
                    # Let's store both full href and base href?
                    # The spine item file_name is usually the relative path.
                    href = item.href.split('#')[0]
                    mapping[href] = item.title
                    if hasattr(item, 'children'):
                        traverse(item.children)
        traverse(self.book.toc)
        return mapping

    def extract_metadata(self):
        """Extracts basic metadata from the EPUB."""
        # Helper to get metadata safely
        def get_meta(namespace, name):
            data = self.book.get_metadata(namespace, name)
            if data:
                return data[0][0]
            return None

        self.metadata['title'] = get_meta('DC', 'title') or "Untitled"
        self.metadata['author'] = get_meta('DC', 'creator') or "Unknown Author"
        self.metadata['language'] = get_meta('DC', 'language') or "en"

    def convert_html_to_md(self, html_content):
        """
        Converts HTML content to Markdown.
        Handles specific cleanup if necessary.
        """
        # 1. Parse with BeautifulSoup to get body content only
        soup = BeautifulSoup(html_content, 'html.parser')
        body = soup.body
        if body:
            content = str(body) # Get inner structure of body
            # Or construct a new cleaner HTML?
            # markdownify handles tags well.
            # But we want to avoid <html><body> wrappers and xml decl.
            # Passing soup object directly? markdownify expects string.
            # content of body is what we want.
            # Actually markdownify might expect full html to handle structure, but body is fine.
            # Only issue is if we pass '<body>...</body>', it's fine.
            clean_html = str(body)
        else:
            clean_html = str(soup) # Fallback

        # 2. Convert
        md_text = md(clean_html, heading_style="ATX", newline_style="BACKSLASH")
        
        # 3. Post-process to clean up excessive newlines or artifacts
        # Remove XML declaration if it persists (unlikely with soup)
        md_text = re.sub(r'<\?xml.*?\?>', '', md_text)
        
        return md_text.strip()

    def _get_item_content(self, item):
        """Decodes content from an EPUB item."""
        try:
            return item.get_content().decode('utf-8')
        except:
            return ""

    def save_project(self, output_dir):
        """
        Extracts content and saves it to the output directory 
        in the md2epub project structure.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        images_dir = output_path / "images"
        images_dir.mkdir(exist_ok=True)

        # 1. Extract Images
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                # Save image
                image_name = os.path.basename(item.file_name)
                with open(images_dir / image_name, 'wb') as f:
                    f.write(item.get_content())
                
                # Check cover
                if 'cover' in image_name.lower():
                     self.metadata['cover_image'] = f"images/{image_name}"

        # 2. Extract Spine Items
        chapter_counter = 1
        
        for item_ref in self.book.spine:
            # item_ref is (item_id, linear)
            item = self.book.get_item_with_id(item_ref[0])
            
            if not item:
                continue
                
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = self._get_item_content(item)
                
                # Identify Title
                # Try map first
                item_href = item.file_name
                title = self.href_to_title.get(item_href)
                
                # If no title in map, try to extract from content (h1)
                if not title:
                    lines = self.convert_html_to_md(html_content).split('\n')
                    for line in lines[:5]:
                        if line.startswith('# '):
                            title = line[2:].strip()
                            break
                            
                if not title:
                    title = f"Chapter {chapter_counter}"

                # Check for cover in filename to skip
                if 'cover' in item.file_name.lower():
                    continue

                # Check for empty content
                markdown_content = self.convert_html_to_md(html_content)
                if not markdown_content.strip():
                    continue
                
                # Improve formatting:
                # If the markdown doesn't start with the title, and it is a Chapter, maybe add it?
                # User's preference varies.
                # But for now, we just save content.

                # Determine if Front Matter or Chapter
                lower_title = title.lower()
                is_front_matter = any(x in lower_title for x in ['title page', 'copyright', 'dedication', 'acknowledgement', 'epigraph', 'about the author', 'toc', 'table of contents'])
                
                # Filename generation
                if is_front_matter:
                    slug = simple_slugify(title) or "front_matter"
                    filename = f"{slug}.md"
                    
                    # Special Case: TOC
                    # If this is the TOC page, we might want to skip it in the yaml if it's auto-generated?
                    # But extracting it is safer so user can edit.
                    # EPUB TOC is usually generated from NCX/Nav. 
                    # If there's a hardcoded HTML TOC, it's just a page.
                    # We add it to front_matter.
                    self.front_matter.append(filename)
                else:
                    # Chapter
                    # Use sequential naming for chapters to keep order obvious?
                    # Or use title slug?
                    # "chapter_01.md" is nice.
                    # If title is "Chapter 1: Ambient Temperature", slug is "chapter-1-ambient-temperature".
                    # Let's stick to "chapter_XX.md" style if possible, or append slug?
                    # "chapter_01_ambient_temperature.md"
                    slug = simple_slugify(title)
                    filename = f"chapter_{chapter_counter:02d}_{slug}.md" if slug else f"chapter_{chapter_counter:02d}.md"
                    self.chapters.append(filename)
                    chapter_counter += 1
                
                # Write file
                with open(output_path / filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

        # 3. Write metadata.yaml
        yaml_content = {
            'title': self.metadata.get('title'),
            'author': self.metadata.get('author'),
            'language': self.metadata.get('language'),
            'cover_image': self.metadata.get('cover_image', ''),
            'front_matter': self.front_matter,
            'chapters': self.chapters
        }
        
        with open(output_path / 'metadata.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, sort_keys=False)

