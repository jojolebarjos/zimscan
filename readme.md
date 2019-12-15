
# ZIM Scan
 
 * [ZIM file format](https://openzim.org/wiki/ZIM_file_format)
 * [Kiwix ZIM repository](http://download.kiwix.org/zim/)
 * [Wikipedia ZIM dumps](https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/)

```python
from zimscan import Reader

with Reader(open('wikipedia_en_all_nopic_2019-10.zim', 'rb')) as reader:
    for record in reader:
        data = record.read()
        ...
```
