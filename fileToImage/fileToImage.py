from PIL import Image
import argparse
import math
import uuid
import os.path

MAX_SIDE_PIXEL = 4062
BYTE_PER_PIXEL = 4
UUID_SIZE = 16
MAX_FILE_NAME_SIZE = 128
SEQUENTIAL_NUMBER_SIZE = 1
FILE_SIZE_SIZE = 8
NAMELEN_SIZE = 1
HEADER_SIZE = 1

class Header:
    def __init__(self):
        self.filename = b''
        self.uuid = uuid.uuid4()
        self.seqnum = 1
        self.lastseqnum = 0
        self.filesize = 0
        self.bodysize = 0
        self.headersize = 0
        self.padding = 0

    def set_file_name(self, name_as_str):
        name_as_bytes = name_as_str.encode()
        self.filename = name_as_bytes[:MAX_FILE_NAME_SIZE]

    def calculate_header_size(self):
        size = UUID_SIZE + SEQUENTIAL_NUMBER_SIZE * 2 + \
            (FILE_SIZE_SIZE * 2) + HEADER_SIZE + NAMELEN_SIZE + len(self.filename)
        self.padding = (BYTE_PER_PIXEL - (size % BYTE_PER_PIXEL)) % BYTE_PER_PIXEL
        self.headersize = size + self.padding

    def get_size(self):
        self.calculate_header_size()
        return self.headersize

    def set_file_size(self, size):
        max_body_size = math.pow(MAX_SIDE_PIXEL, 2) * BYTE_PER_PIXEL - self.get_size()
        num_of_file = math.ceil(size / max_body_size)
        self.filesize = size
        self.lastseqnum = num_of_file

    def to_bytes(self):
        self.calculate_header_size()
        buff = bytearray()
        buff += self.uuid.bytes
        buff += self.seqnum.to_bytes(SEQUENTIAL_NUMBER_SIZE, byteorder='little')
        buff += self.lastseqnum.to_bytes(SEQUENTIAL_NUMBER_SIZE, byteorder='little')
        buff += self.filesize.to_bytes(FILE_SIZE_SIZE, byteorder='little')
        buff += self.bodysize.to_bytes(FILE_SIZE_SIZE, byteorder='little')
        buff += self.headersize.to_bytes(HEADER_SIZE, byteorder='little')
        buff += len(self.filename).to_bytes(1, byteorder='little')
        buff += self.filename
        buff += bytes(self.padding)
        return bytes(buff)

def get_file_size(f):
    file_size = f.seek(0, 2)
    f.seek(0, 0)
    return file_size


def create_image_file(header, input_file):
    read_size = int(math.pow(MAX_SIDE_PIXEL, 2) * BYTE_PER_PIXEL) - header.get_size()
    if (header.seqnum == header.lastseqnum):
        read_size = (header.filesize - input_file.tell())
    header.bodysize = read_size

    data = bytearray()
    data += header.to_bytes()
    data += input_file.read(read_size)

    required_pixel = math.ceil(len(data) / BYTE_PER_PIXEL)
    side_len = math.ceil(math.sqrt(required_pixel));
    required_size = math.pow(side_len, 2) * BYTE_PER_PIXEL;
    while (len(data) < required_size):
        data += b'\0'
    buff = bytes(data)
    image = Image.frombytes('RGBA', (side_len, side_len), buff)
    out_filename = header.uuid.hex + '_' + str(header.seqnum) + '.png'
    image.save(out_filename)


def create_image_files(header, input_file):
    for i in range(1, header.lastseqnum + 1):
        header.seqnum = i
        create_image_file(header, input_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file_path', action='store', type=str, help='File Path')
    args = parser.parse_args()

    input_file = open(args.in_file_path, "rb")
    input_file_size = get_file_size(input_file)
    h = Header()
    h.set_file_name(os.path.basename(args.in_file_path))
    h.set_file_size(input_file_size)

    create_image_files(h, input_file)

if __name__ == '__main__':
    main()
    