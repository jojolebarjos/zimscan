import io
import os


class BufferedFile(io.RawIOBase):
    """A read-only seekable buffer.

    This is similar to `io.BufferedReader`, but will not seek if this is not required.

    """

    def __init__(self, file, *, buffer_size=io.DEFAULT_BUFFER_SIZE):
        # TODO should we also handle non-seekable files?
        self.file = file
        self.buffer = memoryview(bytearray(buffer_size))
        self.buffer_offset = file.tell()
        self.offset = 0
        self.length = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.buffer_offset + self.offset

    def readinto(self, buffer):

        # Read chunks, until request is fulfilled
        offset = 0
        length = len(buffer)
        while offset < length:

            # Copy chunk
            n = min(self.length - self.offset, length - offset)
            buffer[offset : offset + n] = self.buffer[self.offset : self.offset + n]
            offset += n
            self.offset += n

            # Stop, if request is fulfilled
            if offset >= length:
                break

            # Refill buffer
            self.buffer_offset += self.length
            self.length = self.file.readinto(self.buffer)
            self.offset = 0

            # Check for end-of-file
            if self.length <= 0:
                break

        return offset

    def seek(self, offset, whence=os.SEEK_SET):

        # Get absolute offset, if possible
        if whence == os.SEEK_CUR:
            offset += self.tell()
            whence = os.SEEK_SET

        # Can only optimize absolute offset
        if whence == os.SEEK_SET:

            # If desired location is within buffer boundaries, just move pointer
            if self.buffer_offset <= offset <= self.buffer_offset + self.length:
                self.offset = offset - self.buffer_offset
                return offset

        # Otherwise, seek and invalidate buffer
        # TODO if not far ahead, maybe a read operation would be cheaper?
        self.buffer_offset = self.file.seek(offset, whence)
        self.offset = 0
        self.length = 0
        return self.buffer_offset
