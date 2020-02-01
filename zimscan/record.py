
import io


# Archive entry container
class Record(io.RawIOBase):
    """ZIM article.

    This is a binary, read-only and non-seekable file-like. It is invalidated
    when the next record is requested.

    """

    def __init__(self, file, length):
        # TODO metadata (title, url, mimetype, namespace, revision)
        # TODO should we also provide non-article directories (i.e. redirect, linktarget, deleteditem)?
        self._file = file
        self._remaining = length

    # Read-only
    def readable(self):
        return True

    # Everything else is already implemented in abstract parent
    def readinto(self, buffer):

        # Check that we are still allowed to read
        if self._file is None or self.closed:
            raise RuntimeError('Cannot read from invalidated record')

        # Make sure we do not read more than our blob
        requested = len(buffer)
        if requested > self._remaining:
            buffer = memoryview(buffer)[:self._remaining]

        # Ask underlying file for content
        size = self._file.readinto(buffer)
        self._remaining -= size
        return size
