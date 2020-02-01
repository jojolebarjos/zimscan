
# ZIM Scan

Minimal ZIM file reader, designed for article streaming.


## Getting Started

Install using pip:

```
pip install git+https://gitlab.com/jojolebarjos/zimscan.git
```

Iterate over a records, which are binary file-like objects:

```python
from zimscan import Reader

with Reader(open('wikipedia_en_all_nopic_2019-10.zim', 'rb')) as reader:
    for record in reader:
        data = record.read()
        ...
```


## Links

 * [ZIM file format](https://openzim.org/wiki/ZIM_file_format)
 * [Kiwix ZIM repository](http://download.kiwix.org/zim/)
 * [Wikipedia ZIM dumps](https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/)
 * [ZIMply](https://github.com/kimbauters/ZIMply), a ZIM file reader in the browser, in Python
 * [libzim](https://github.com/openzim/libzim), the reference implementation, in C++
 * [pyzim](https://github.com/pediapress/pyzim), Python wrapper for libzim
 * [pyzim](https://framagit.org/mgautierfr/pyzim), another Python wrapper for libzim
 * [Internet In A Box](https://github.com/iiab/internet-in-a-box)
