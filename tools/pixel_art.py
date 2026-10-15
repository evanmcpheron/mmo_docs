"""Small integer raster and Aseprite writer for reproducible original references."""
from __future__ import annotations
import struct
import zlib


def rgba(color):
    if isinstance(color, str):
        value = bytes.fromhex(color.lstrip('#'))
        return tuple(value) + (255,) if len(value) == 3 else tuple(value)
    return tuple(color)


class Raster:
    def __init__(self, width, height, color=(0, 0, 0, 0)):
        self.width, self.height = width, height
        self.pixels = bytearray(rgba(color) * (width * height))

    def pixel(self, x, y, color=None):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return (0, 0, 0, 0)
        index = (y * self.width + x) * 4
        if color is None:
            return tuple(self.pixels[index:index + 4])
        self.pixels[index:index + 4] = bytes(rgba(color))

    def rect(self, x, y, width, height, color):
        for py in range(y, y + height):
            for px in range(x, x + width):
                self.pixel(px, py, color)

    def line(self, x1, y1, x2, y2, color):
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
        error = dx + dy
        while True:
            self.pixel(x1, y1, color)
            if (x1, y1) == (x2, y2):
                break
            twice = error * 2
            if twice >= dy:
                error += dy
                x1 += sx
            if twice <= dx:
                error += dx
                y1 += sy

    def ellipse(self, x, y, width, height, color):
        for py in range(height):
            for px in range(width):
                if ((2 * px + 1 - width) / width) ** 2 + ((2 * py + 1 - height) / height) ** 2 <= 1:
                    self.pixel(x + px, y + py, color)

    def polygon(self, points, color):
        for py in range(min(y for x, y in points), max(y for x, y in points) + 1):
            for px in range(min(x for x, y in points), max(x for x, y in points) + 1):
                inside = False
                previous = points[-1]
                for current in points:
                    x1, y1 = previous
                    x2, y2 = current
                    if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                        inside = not inside
                    previous = current
                if inside:
                    self.pixel(px, py, color)

    def paste(self, other, x, y):
        for py in range(other.height):
            for px in range(other.width):
                color = other.pixel(px, py)
                if color[3]:
                    self.pixel(x + px, y + py, color)

    def crop(self, x, y, width, height):
        result = Raster(width, height)
        for py in range(height):
            for px in range(width):
                result.pixel(px, py, self.pixel(x + px, y + py))
        return result

    def png(self):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
        raw = b''.join(b'\x00' + self.pixels[y * self.width * 4:(y + 1) * self.width * 4] for y in range(self.height))
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', self.width, self.height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')


def read_png(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Not PNG')
    offset, packed = 8, b''
    while offset < len(data):
        size = struct.unpack_from('>I', data, offset)[0]
        kind, body = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + size]
        if zlib.crc32(kind + body) != struct.unpack_from('>I', data, offset + 8 + size)[0]:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            width, height, depth, mode, _, _, interlace = struct.unpack('>IIBBBBB', body)
            if (depth, mode, interlace) != (8, 6, 0):
                raise ValueError('Reference PNG must be noninterlaced RGBA8')
        if kind == b'IDAT':
            packed += body
        offset += size + 12
    raw = zlib.decompress(packed)
    stride = width * 4 + 1
    if len(raw) != height * stride or any(raw[y * stride] for y in range(height)):
        raise ValueError('Unexpected reference PNG scanlines')
    image = Raster(width, height)
    image.pixels = bytearray(b''.join(raw[y * stride + 1:(y + 1) * stride] for y in range(height)))
    return image


def aseprite(layers, frames, durations, tags=()):
    """Write RGBA cels without trimming so all paper-doll layers keep registration."""
    width, height = frames[0][0].width, frames[0][0].height

    def string(value):
        encoded = value.encode('utf-8')
        return struct.pack('<H', len(encoded)) + encoded

    def chunk(kind, body):
        return struct.pack('<IH', len(body) + 6, kind) + body

    output = []
    for index, images in enumerate(frames):
        chunks = []
        if index == 0:
            for name in layers:
                chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + bytes(3) + string(name)))
            if tags:
                body = struct.pack('<H', len(tags)) + bytes(8)
                for name, start, end in tags:
                    body += struct.pack('<HHBH', start, end, 0, 0) + bytes(6) + bytes(3) + bytes(1) + string(name)
                chunks.append(chunk(0x2018, body))
        for layer, image in enumerate(images):
            body = struct.pack('<HhhBHh', layer, 0, 0, 255, 2, 0) + bytes(5)
            body += struct.pack('<HH', width, height) + zlib.compress(image.pixels, 9)
            chunks.append(chunk(0x2005, body))
        body = b''.join(chunks)
        output.append(struct.pack('<IHHH2sI', len(body) + 16, 0xF1FA, len(chunks), durations[index], bytes(2), 0) + body)
    body = b''.join(output)
    header = struct.pack('<IHHHHH', len(body) + 128, 0xA5E0, len(frames), width, height, 32)
    header += struct.pack('<IHII', 1, durations[0], 0, 0) + bytes(1) + bytes(3) + struct.pack('<HBBhhHH', 0, 1, 1, 0, 0, 16, 16)
    return header.ljust(128, b'\x00') + body
