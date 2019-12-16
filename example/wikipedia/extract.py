
import io
import re
from tqdm import tqdm

from zimscan import Reader

from clean import iterate_paragraphs


# Valid HTML pages are expected to have a canonical link
canonical_regex = re.compile(br'<link rel="canonical" href="([^"]+)">')
ns_regex = re.compile(br'<body class="[^"]*\bns-(\d+)\b[^"]*">')

# Process dump
input_path = 'wikipedia_en_all_nopic_2019-10.zim'
with Reader(io.open(input_path, 'rb')) as reader:

    # Output everything in a single file
    output_path = 'wikipedia.en.txt'
    with io.open(output_path, 'w', encoding='utf-8', newline='\n') as output:
    
        # Iterate over entries
        for record in tqdm(reader):
            content = record.read()
            
            # Find canonical URL as proof of being an HTML page
            match = canonical_regex.search(content, endpos=1000)
            if match is not None:
                url = match.group(1).decode('utf-8')
                
                # Furthermore, only consider pages in namespace 0
                match = ns_regex.search(content)
                if match is not None and match.group(1) == b'0':
                    
                    # Output document as plain text, separated by empty lines
                    output.write(url)
                    output.write('\n')
                    for paragraph in iterate_paragraphs(content):
                        output.write(paragraph)
                        output.write('\n')
                    output.write('\n')
