import io
import lzma
import numpy
import struct

from .record import Record


# Define little-endian integer types
uint8 = numpy.dtype(numpy.uint8).newbyteorder("<")
uint16 = numpy.dtype(numpy.uint16).newbyteorder("<")
uint32 = numpy.dtype(numpy.uint32).newbyteorder("<")
uint64 = numpy.dtype(numpy.uint64).newbyteorder("<")


# Define binary structures
header = struct.Struct("<LHH16sLLQQQQLLQ")


# Archive iterator
class Reader:
    """ZIM archive reader.

    This reader is designed to efficiently iterate through the whole archive.
    Lookup by URL or title is not supported.

    This objects is an iterator with known size, namely the number of articles.

    Args:
        file: Readable and seekable file-like.

    Examples:
        Process a local file, for instance to extract plain text from HTML
        files.

        >>> from zimscan import Reader
        >>> with Reader(open("file.zim", "rb")) as reader:
        ...     for record in reader:
        ...         data = record.read()
        ...         ... # do something

    """

    def __init__(self, file):

        # TODO add parameter to choose whether to get meta (disabled by default)

        # Wrap in buffer, to ensure exact read size
        self._file = io.BufferedReader(file)

        # Read header
        (
            magic,
            major,
            minor,
            self.uuid,
            self._article_count,
            self._cluster_count,
            url_pointer_list_offset,
            title_pointer_list_offset,
            cluster_pointer_list_offset,
            mime_list_offset,
            main_page,
            layout_page,
            checksum_offset,
        ) = header.unpack(self._file.read(header.size))

        # Check format
        if magic != 72173914:
            raise IOError("invalid ZIM file")
        if major != 5 and major != 6:
            raise IOError(f"ZIM format version {major}.{minor} not supported")

        # TODO load MIME type list (only if metadata is requested)
        # TODO load directories, if requested
        # TODO also provide redirects, if directories are available

        # Read cluster pointers
        self._file.seek(cluster_pointer_list_offset)
        self._cluster_pointer_list = numpy.frombuffer(
            self._file.read(8 * self._cluster_count), uint64
        )

        # Iterator state
        self._cluster_index = -1
        self._cluster_file = None
        self._blob_count = 0
        self._blob_index = 0
        self._blob_offsets = None
        self._record = None

    # Number of article is known
    def __len__(self):
        return self._article_count

    # The reader iself is an iterator
    def __iter__(self):
        return self

    # Advance
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
            self._file.seek(self._cluster_pointer_list[self._cluster_index])

            # Read uncompressed cluster header
            (mode,) = numpy.frombuffer(self._file.read(1), uint8)

            # Wrap input based on compression mode
            compression = mode & 0x0F
            if compression == 4:
                self._cluster_file = lzma.open(self._file)
            else:
                self._cluster_file = self._file

            # Detect blob offset size
            if mode & 0b10000:
                offset_type = uint64
            else:
                offset_type = uint32

            # Read first blob offset, used to detect blob count
            data = self._cluster_file.read(offset_type.itemsize)
            (first_blob_offset,) = numpy.frombuffer(data, offset_type)
            blob_offset_count = first_blob_offset // offset_type.itemsize
            self._blob_count = blob_offset_count - 1

            # Read all blob offsets
            self._blob_offsets = numpy.empty(blob_offset_count, offset_type)
            self._blob_offsets[0] = first_blob_offset
            data = self._cluster_file.read(offset_type.itemsize * self._blob_count)
            self._blob_offsets[1:] = numpy.frombuffer(data, offset_type)

        # Prepare record
        length = (
            self._blob_offsets[self._blob_index + 1]
            - self._blob_offsets[self._blob_index]
        )
        self._record = Record(self._cluster_file, length)
        # TODO populate metadata, if requested
        return self._record

    # Close underlying file
    def close(self):
        if self._record is not None:
            self._record._file = None
        self._file.close()

    # Entering context is a no-op
    def __enter__(self):
        return self

    # Close on context exit
    def __exit__(self, type, value, traceback):
        self.close()
