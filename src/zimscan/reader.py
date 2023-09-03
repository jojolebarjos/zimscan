import io
import lzma
import struct

import numpy as np

import zstandard as zstd

from .file import BufferedFile
from .record import Record


# Define little-endian integer types
uint8 = np.dtype(np.uint8).newbyteorder("<")
uint16 = np.dtype(np.uint16).newbyteorder("<")
uint32 = np.dtype(np.uint32).newbyteorder("<")
uint64 = np.dtype(np.uint64).newbyteorder("<")


# Define binary structures
HEADER = struct.Struct("<LHH16sLLQQQQLLQ")
ENTRY_HEADER = struct.Struct("<H")
CONTENT_ENTRY = struct.Struct("<BcIII")


class Reader:
    """ZIM archive reader.

    This reader is designed to efficiently iterate through the whole archive. Lookup by
    URL or title is not supported.

    This objects is an iterator with known size, namely the number of articles.

    Args:
        file: Readable and seekable file-like.

    Examples:
        Process a local file, for instance to extract plain text from HTML files.

        >>> from zimscan import Reader
        >>> with Reader(open("file.zim", "rb")) as reader:
        ...     for record in reader:
        ...         data = record.read()
        ...         ... # do something

    """

    def __init__(
        self,
        file,
        *,
        skip_metadata=False,
        buffer_size=io.DEFAULT_BUFFER_SIZE,
    ):

        # Wrap in buffer, to ensure exact read size
        self._file = BufferedFile(file, buffer_size=buffer_size)
        self._zero_offset = self._file.tell()

        # Read header
        (
            magic,
            major,
            minor,
            self.uuid,
            self._entry_count,
            self._cluster_count,
            self._url_pointer_list_offset,
            self._title_pointer_list_offset,
            self._cluster_pointer_list_offset,
            self._mime_list_offset,
            self._main_page,
            self._layout_page,
            self._checksum_offset,
        ) = HEADER.unpack(self._file.read(HEADER.size))

        # Check format
        if magic != 72173914:
            raise IOError("invalid ZIM file")
        if major not in (5, 6):
            raise IOError(f"ZIM format version {major}.{minor} not supported")

        # Collect directory entries, if requested
        self._directories = None
        if not skip_metadata:

            # Load MIME type list
            # Note: this should always be just after the header
            self._file.seek(self._zero_offset + self._mime_list_offset)
            mime_types = []
            while True:
                mime_type = _read_string(self._file)
                if not mime_type:
                    break
                mime_types.append(mime_type)

            # Load URL pointer list
            self._file.seek(self._zero_offset + self._url_pointer_list_offset)
            url_pointer_list = np.frombuffer(
                self._file.read(8 * self._entry_count), uint64
            )

            # Load directories
            directory_offsets = np.sort(url_pointer_list)
            self._directories = {}
            for offset in directory_offsets:
                self._file.seek(self._zero_offset + int(offset))

                # Get MIME type
                (mime_type_index,) = ENTRY_HEADER.unpack(
                    self._file.read(ENTRY_HEADER.size)
                )

                # Ignore link target, deleted entries, and redirects
                # TODO is there a meaningful way to provide redirects?
                if mime_type_index in (0xFFFE, 0xFFFD, 0xFFFF):
                    continue

                # Decode the remaining part of the content entry metadata
                (
                    parameter_length,
                    namespace,
                    revision,
                    cluster_index,
                    blob_index,
                ) = CONTENT_ENTRY.unpack(self._file.read(CONTENT_ENTRY.size))
                url = _read_string(self._file)
                title = _read_string(self._file)

                # Collect relevant metadata for later
                mime_type = mime_types[mime_type_index]
                key = cluster_index, blob_index
                value = namespace.decode("ascii"), mime_type, url, title, revision
                self._directories[key] = value

        # Read cluster pointers
        self._file.seek(self._zero_offset + self._cluster_pointer_list_offset)
        self._cluster_pointer_list = np.frombuffer(
            self._file.read(8 * self._cluster_count), uint64
        )

        # Iterator state
        self._cluster_index = -1
        self._cluster_file = None
        self._blob_count = 0
        self._blob_index = 0
        self._blob_offsets = None
        self._record = None

        # Instanciate zstandard decompressor once for all
        self._zstd_decompressor = zstd.ZstdDecompressor()

    def __len__(self):
        if self._directories is None:
            return NotImplemented
        return len(self._directories)

    def __iter__(self):
        return self

    def __next__(self):

        # Invalidate current record, if any
        if self._record is not None:
            if self._record._remaining > 0:
                self._cluster_file.seek(self._record._remaining, io.SEEK_CUR)
            self._record._file = None
            self._record = None
        self._blob_index += 1

        # If current cluster is exhausted, advance to next cluster
        while self._blob_index >= self._blob_count:
            self._cluster_index += 1
            if self._cluster_index >= self._cluster_count:
                raise StopIteration
            self._blob_index = 0

            # Move to cluster
            self._file.seek(
                self._zero_offset + int(self._cluster_pointer_list[self._cluster_index])
            )

            # Read uncompressed cluster header
            (mode,) = np.frombuffer(self._file.read(1), uint8)

            # Wrap input based on compression mode
            compression = mode & 0x0F
            if compression == 1:
                self._cluster_file = self._file
            elif compression == 4:
                self._cluster_file = lzma.open(self._file)
            elif compression == 5:
                self._cluster_file = self._zstd_decompressor.stream_reader(self._file)
            else:
                raise KeyError(compression)

            # Detect blob offset size
            if mode & 0b10000:
                offset_type = uint64
            else:
                offset_type = uint32

            # Read first blob offset, used to detect blob count
            data = self._cluster_file.read(offset_type.itemsize)
            (first_blob_offset,) = np.frombuffer(data, offset_type)
            blob_offset_count = first_blob_offset // offset_type.itemsize
            self._blob_count = blob_offset_count - 1

            # Read all blob offsets
            self._blob_offsets = np.empty(blob_offset_count, offset_type)
            self._blob_offsets[0] = first_blob_offset
            data = self._cluster_file.read(offset_type.itemsize * self._blob_count)
            self._blob_offsets[1:] = np.frombuffer(data, offset_type)

        # Prepare record
        length = (
            self._blob_offsets[self._blob_index + 1]
            - self._blob_offsets[self._blob_index]
        )
        if self._directories is None:
            record = Record(self._cluster_file, length)
        else:
            key = self._cluster_index, self._blob_index
            value = self._directories[key]
            namespace, mime_type, url, title, revision = value
            record = Record(
                self._cluster_file,
                length,
                mime_type,
                namespace,
                url,
                title,
                revision,
            )

        self._record = record
        return record

    def close(self):
        if self._record is not None:
            self._record._file = None
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


def _read_string(file):
    buffer = bytearray()
    while True:
        byte = file.read(1)
        if not byte:
            raise IOError("Unterminated string")
        if byte == b"\0":
            break
        buffer.extend(byte)
    return buffer.decode("utf-8")
