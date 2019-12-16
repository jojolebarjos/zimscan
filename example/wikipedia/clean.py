
from lxml import html
import re


# Special marker for paragraph splits
split = object()


# Keep track of unexpected tags
unknown_tags = set()


# Cleaning regexes
whitespace_regex = re.compile(r'\s+')
references_regex = re.compile(r'\[\d+\]')


# Get all text fragments
def iterate_chunks(element):
    
    # Helper
    def chunks(emit_content=False, emit_split=False):
        if emit_split:
            yield split
        if emit_content:
            if element.text:
                yield element.text
            for child in element:
                yield from iterate_chunks(child)
        if emit_split:
            yield split
        if element.tail:
            yield element.tail
    
    # Ignore comments and unexpected objects
    if type(element.tag) is not str:
        yield from chunks()
    
    # Structural element marks paragraph split
    # TODO should maybe preserve dashes/numbers in lists?
    # TODO or maybe, just ignore lists, as these are often short and incomplete
    elif element.tag in {
        'blockquote',    # Quotation
        'body',          # Main HTML body
        'dd',            # Description item
        'details',       # Additional details that the user can view or hide on demand
        'div',           # Structural element
        'dl',            # Description list container
        'dt',            # Term item
        'li',            # List item
        'ol',            # Ordered list container
        'p',             # Paragraph
        'ul',            # Unordered list container
    }:
        yield from chunks(emit_content=True, emit_split=True)
        
    # TODO h2, h3...

    # Handle line break
    elif element.tag == 'br':
        yield '\n'
    
    # Remove tag, keep content
    elif element.tag in {
        
        # Common formats
        'b',             # Bold
        'em',            # Emphasis (often rendered as italic)
        'i',             # Italic
        's',             # Strikethrough
        'span',          # Generic structure used to apply custom formatting, stripped as it is too complicated too handle
        'sub',           # Subscript
        'sup',           # Superscript
        'u',             # Underline
        
        # Links and quotations
        'a',             # Link
        'cite',          # Reference citation (mostly used for footnotes)
        'q',             # Inline quotation
        
        # Rich content markers
        'abbr',          # Abbreviation
        'time',          # Time
        
        # Code-like formats
        'code',          # Inline code snippet, usually for variables or short commands
        'kbd',           # Mark used for keys (can be considered as code)
        'tt',            # Typescript, usually rendered as monospaced characters
        'var',           # Variable marker, usually rendered as code
        
        # Uncommon formats
        'bdi',           # Bi-directional isolation, used to handle mixed text orientation (probably useless in this usage)
        'big',           # Emphasis-like
        'del',           # Mark for removed/deprecated text, rendered as strikethrough
        'dfn',           # Emphases, usually rendered as bold
        'font',          # Font, mostly used to define text color
        'ins',           # Mark for newly inserted text, usually used for revisions
        'mark',          # Highlight, usually used for revisions
        'rb',            # Ruby-related, base marker (this is the only one kept, as it is the actual content)
        'ruby',          # Ruby is used to annotate glyphs (usually Asian languages)
        'section',       # Used as container in some language (e.g. latin)
        'small',         # Emphasis-like
        'strong',        # Emphasis, usually rendered as bold
        'wbr',           # Word break opportunity, irrelevant for plain text corpora
    }:
        yield from chunks(emit_content=True)
    
    # Remove both tag and content
    elif element.tag in {
        'audio',         # Embedded audio player
        'center',        # Centered block (usually used for banners, i.e. don't care)
        'figure-inline', # ??? (occured in latin dump)
        'hr',            # Horizontal rule (or topic change)
        'img',           # Embedded image
        'math',          # Formulas
        'meta',          # Invisible properties
        'pre',           # Preserve plain text formatting, usually for code snippet (ignored for simplicity)
        'rp',            # Ruby-related, fallback parenthesis
        'rt',            # Ruby-related, pronunciation
        'rtc',           # Ruby-related, semantic annotation
        'script',        # Embedded JS code
        'style',         # Embedded CSS code
        'table',         # Table (removed for simplicity)
    }:
        yield from chunks()
    
    # Report unknown tag (and remove both tag and content)
    else:
        unknown_tags.add(element.tag)
        yield from chunks()


# Get all paragraphs
def iterate_paragraphs(tree):
    buffer = []
    for chunk in iterate_chunks(tree.body):
        if chunk is split:
            text = ''.join(buffer)
            text = references_regex.sub(' ', text)
            text = whitespace_regex.sub(' ', text)
            text = text.strip()
            # TODO maybe ignore stuff in "See also", "References", "External links", "Notes"
            # TODO add length/sanity check (e.g. min length, need to end with punctuation, ratio of punctuation/latin chars/digits)
            # TODO ignore page with "may refer to"?
            if text and not text.startswith('This article is issued from Wikipedia.'):
                yield text
            buffer.clear()
        else:
            buffer.append(chunk)


# Parse and clean text
def extract_text(content):
    tree = html.fromstring(content)
    text = '\n'.join(iterate_paragraphs(tree))
    return text
