
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
import io
import re
from tqdm import tqdm

from zimscan import Reader

from clean import extract_text
from worker import lazy_map


# Valid HTML pages are expected to have a namespace
ns_regex = re.compile(br'<body class="[^"]*\bns-(\d+)\b[^"]*">')


# Iterate articles
def iterate_contents(reader):
    for record in reader:
        content = record.read()
        match = ns_regex.search(content)
        if match is not None and match.group(1) == b'0':
            yield content


# Spawn pool
with ProcessPoolExecutor() as executor:

    # Process dump
    input_path = 'wikipedia_en_all_nopic_2019-10.zim'
    with Reader(io.open(input_path, 'rb')) as reader:

        # Output everything in a single file
        output_path = 'wikipedia.en.txt'
        with io.open(output_path, 'w', encoding='utf-8', newline='\n') as output:
            
            # Wrap in parallel executor
            iterator = iterate_contents(reader)
            iterator = (partial(extract_text, content) for content in iterator)
            iterator = lazy_map(iterator, executor)
            
            for text in tqdm(iterator, total=len(reader)):
                
                # Output document as plain text, separated by empty lines
                output.write(text)
                output.write('\n\n')
