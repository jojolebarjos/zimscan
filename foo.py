

import io
import numpy
import struct

from tqdm import tqdm


uint8 = numpy.dtype(numpy.uint8).newbyteorder('<')
uint16 = numpy.dtype(numpy.uint16).newbyteorder('<')
uint32 = numpy.dtype(numpy.uint32).newbyteorder('<')
uint64 = numpy.dtype(numpy.uint64).newbyteorder('<')


def read_string(file):
    buffer = []
    while True:
        byte = file.read(1)
        if len(byte) == 0 or byte == b'\x00':
            break
        buffer.extend(byte)
    return bytes(buffer).decode('utf-8')


file = io.open('wikipedia_en_all_nopic_2019-10.zim', 'rb')

(
    magic,
    major,
    minor,
    uuid,
    article_count,
    cluster_count,
    url_pointer_list_offset,
    title_pointer_list_offset,
    cluster_pointer_list_offset,
    mime_list_offset,
    main_page,
    layout_page,
    checksum_offset
) = struct.unpack('<LHH16sLLQQQQLLQ', file.read(80))

if magic != 72173914:
    raise IOError('invalid ZIM file')

if major != 5 and major != 6:
    raise IOError(f'ZIM format version {major}.{minor} not supported')


assert mime_list_offset == 80

mime_types = []
while True:
    mime_type = read_string(file)
    if len(mime_type) == 0:
        break
    mime_types.append(mime_type)



# TODO except MIME list, which is guaranteed to be directly after the header, need to check for gap/reordering of over chunks?


assert file.tell() == url_pointer_list_offset

buffer = file.read(8 * article_count)
directory_offsets = numpy.frombuffer(buffer, uint64).copy()
directory_offsets.sort()


assert file.tell() == title_pointer_list_offset

# discard title pointers
_ = file.read(4 * article_count)





for i in tqdm(range(article_count)):
    
    assert file.tell() == directory_offsets[i]
    
    (
        mime_type_index,
        parameter_size,
        namespace,
        revision
    ) = struct.unpack('<HBBL', file.read(8))
    
    # redirect
    if mime_type_index == 0xffff:
        redirect_index = struct.unpack('<L', file.read(4))
    
    # linktarget
    elif mime_type_index == 0xfffe:
        pass
    
    # deleted entry
    elif mime_type_index == 0xfffd:
        pass
    
    # article
    else:
        (
            cluster_index,
            blob_index
        ) = struct.unpack('<LL', file.read(8))
    
    url = read_string(file)
    title = read_string(file)
    
    if parameter_size:
        _ = file.read(parameter_size)


assert file.tell() == cluster_pointer_list_offset

buffer = file.read(8 * cluster_count)
cluster_offsets = numpy.frombuffer(buffer, uint64).copy()
cluster_offsets.sort()


for i in tqdm(range(cluster_count)):
    
    assert file.tell() == cluster_offsets[i]
    
    cluster_info, = struct.unpack('>B', file.read(1))
    compression = cluster_info & 0x0f
    offset_size = 8 if cluster_info & 0b10000 else 4
    
    # LZMA2
    if compression == 4:
        pass
    
    # no compression
    else:
        pass
    
    # TODO do on uncompressed cluster!
    
    first_blob_offset = file.read(offset_size)
    blob_count = first_blob_offset // offset_size
    blob_offsets = numpy.empty(blob_count, uint32) # TODO use offset_size
    blob_offsets[0] = first_blob_offset
    blob_offsets[1:] = numpy.frombuffer(file.read(offset_size * (blob_count - 1)), uint32) # TODO use offset_size
    
    for j in range(blob_count):
        pass
        # TODO find blob in directories
        # TODO yield record, as file like with extra


assert file.tell() == checksum_offset

# TODO read/test checksum?


# TODO namespace mapping?

# TODO URL resolution helper?



