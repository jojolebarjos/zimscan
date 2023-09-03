# ZIM Scan

Minimal ZIM file reader, designed for article streaming.


## Getting Started

Install using pip:

```
pip install zimscan
```

Or from Git repository, for latest version:

```
pip install -U git+https://github.com/jojolebarjos/zimscan.git
```

Iterate over a records, which are binary file-like objects:

```python
from zimscan import Reader

path = "wikipedia_en_all_nopic_2019-10.zim"
with Reader(open(path, "rb"), skip_metadata=True) as reader:
    for record in reader:
        data = record.read()
        ...
```


## Links

 * [ZIM file format](https://openzim.org/wiki/ZIM_file_format), official documentation
 * [Kiwix ZIM repository](http://download.kiwix.org/zim/), to download official ZIM files
 * [Wikipedia ZIM dumps](https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/), to download Wikipedia ZIM files
 * [ZIMply](https://github.com/kimbauters/ZIMply), a ZIM file reader in the browser, in Python
 * [libzim](https://github.com/openzim/libzim), the reference implementation, in C++
 * [pyzim](https://github.com/pediapress/pyzim), Python wrapper for libzim
 * [pyzim](https://framagit.org/mgautierfr/pyzim), another Python wrapper for libzim
 * [Internet In A Box](https://github.com/iiab/internet-in-a-box), a project to bundle open knowledge locally
