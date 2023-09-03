import io
import os

from zimscan import BufferedFile


class LoggedBytesIO(io.BytesIO):
    def __init__(self, *args):
        super().__init__(*args)
        self.readinto_count = 0
        self.seek_count = 0

    def readinto(self, buffer):
        self.readinto_count += 1
        return super().readinto(buffer)

    def seek(self, offset, whence=os.SEEK_SET):
        self.seek_count += 1
        return super().seek(offset, whence)


def test_buffered_file():

    data = b"abcdefghijklmnopqrstuvwxyz"
    file = LoggedBytesIO(data)
    buffered_file = BufferedFile(file, buffer_size=5)

    assert file.readinto_count == 0
    assert file.seek_count == 0

    assert buffered_file.read(2) == b"ab"
    assert file.readinto_count == 1
    assert file.seek_count == 0

    assert buffered_file.read(3) == b"cde"
    assert file.readinto_count == 1
    assert file.seek_count == 0

    assert buffered_file.read(1) == b"f"
    assert file.readinto_count == 2
    assert file.seek_count == 0

    assert buffered_file.read(9) == b"ghijklmno"
    assert file.readinto_count == 3
    assert file.seek_count == 0

    assert buffered_file.seek(12) == 12
    assert file.readinto_count == 3
    assert file.seek_count == 0

    assert buffered_file.read(3) == b"mno"
    assert file.readinto_count == 3
    assert file.seek_count == 0

    assert buffered_file.seek(1, os.SEEK_CUR) == 16
    assert file.readinto_count == 3
    assert file.seek_count == 1

    assert buffered_file.read(10) == b"qrstuvwxyz"
    assert file.readinto_count == 5
    assert file.seek_count == 1

    assert buffered_file.read(1) == b""
