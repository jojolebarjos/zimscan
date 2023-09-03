"""Extract IPA notation from Wiktionary.

This is an example script, with limited capabilities. In particular, language
is not extracted. Moreover, only the main title is registered.

"""


import argparse
import re
from tqdm import tqdm

from zimscan import Reader


# Compile useful regexes
title_r = re.compile(rb"<title>([^<]+)</title>")
ipa_r = re.compile(rb"<span class=\"IPA\">(.*?)</span>")
whitespace_r = re.compile(r"\s+")


# Clean UTF-8 bytes
def clean_bytes(value):
    value = value.decode("utf-8")
    value = whitespace_r.sub(" ", value)
    value = value.strip()
    return value


# Define command-line parser
parser = argparse.ArgumentParser(description="Extract IPA from Wiktionary")
parser.add_argument("input_path", help="ZIM input path")
parser.add_argument("output_path", help="TSV output path")


# Standalone usage
if __name__ == "__main__":
    args = parser.parse_args()

    # Open output TSV file
    with open(args.output_path, "w", encoding="utf-8", newline="\n") as file:
        file.write("title\tipa\n")

        # Stream records
        with Reader(open(args.input_path, "rb"), skip_metadata=True) as reader:
            for record in tqdm(reader):

                # Get all bytes
                data = record.read()

                # Find title, if any
                match = title_r.search(data)
                if match:
                    title = clean_bytes(match.group(1))
                    if title:

                        # Find IPA banners, if any
                        for match in ipa_r.finditer(data):
                            ipa = clean_bytes(match.group(1))
                            if ipa:

                                # Write output
                                file.write(f"{title}\t{ipa}\n")
