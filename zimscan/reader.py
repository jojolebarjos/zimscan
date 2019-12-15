
import io
import lzma
import numpy
import struct

from .record import Record


uint8 = numpy.dtype(numpy.uint8).newbyteorder('<')
uint16 = numpy.dtype(numpy.uint16).newbyteorder('<')
uint32 = numpy.dtype(numpy.uint32).newbyteorder('<')
uint64 = numpy.dtype(numpy.uint64).newbyteorder('<')

header = struct.Struct('<LHH16sLLQQQQLLQ')


class Reader:
    ''' ZIM archive reader.
    
    This reader is designed to efficiently iterate through the whole archive.
    Lookup by URL or title is not supported.
    
    '''
    
    def __init__(self, file):
        
        # Wrap in buffer, to ensure exact read size
        self.file = io.BufferedReader(file)
        
        # Read header
        (
            self.magic,
            self.major,
            self.minor,
            self.uuid,
            self.article_count,
            self.cluster_count,
            self.url_pointer_list_offset,
            self.title_pointer_list_offset,
            self.cluster_pointer_list_offset,
            self.mime_list_offset,
            self.main_page,
            self.layout_page,
            self.checksum_offset
        ) = header.unpack(self.file.read(header.size))
        
        # Read cluster pointers
        self.file.seek(self.cluster_pointer_list_offset)
        self.cluster_pointer_list = numpy.frombuffer(self.file.read(8 * self.cluster_count), uint64)
    
    def __len__(self):
        return self.article_count
    
    def __iter__(self):
        
        # For each cluster...
        for cluster_index in range(self.cluster_count):
            
            # Move to cluster
            self.file.seek(self.cluster_pointer_list[cluster_index])
            
            # Read uncompressed cluster header
            mode, = numpy.frombuffer(self.file.read(1), uint8)
            
            # Wrap input based on compression mode
            compression = mode & 0x0f
            if compression == 4:
                file = lzma.open(self.file)
            else:
                file = self.file
            
            # Detect blob offset size
            if mode & 0b10000:
                offset_type = uint64
            else:
                offset_type = uint32
            
            # Read first blob offset, used to detect blob count
            first_blob_offset, = numpy.frombuffer(file.read(offset_type.itemsize), offset_type)
            blob_count = first_blob_offset // offset_type.itemsize
            blob_offsets = numpy.empty(blob_count, offset_type)
            blob_offsets[0] = first_blob_offset
            blob_offsets[1:] = numpy.frombuffer(file.read(offset_type.itemsize * (blob_count - 1)), offset_type)
            
            # For each blob...
            for blob_index in range(blob_count):
                
                # Prepare record
                length = blob_offsets[blob_index + 1] - blob_offsets[blob_index]
                record = Record(file, length)
                yield record
                
                # Consume remaining bytes
                if record._remaining > 0:
                    file.seek(record._remaining, io.SEEK_CUR)
                
                # Invalidate record as soon as we continue
                record._file = None
    
    def close(self):
        self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
