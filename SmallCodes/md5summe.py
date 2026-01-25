import struct
import math

class MD5:
    """Educational implementation of MD5 hash algorithm"""

    def __init__(self):
        # MD5 constants - initial hash values (A, B, C, D)
        self.A = 0x67452301
        self.B = 0xEFCDAB89
        self.C = 0x98BADCFE
        self.D = 0x10325476

        # Pre-computed sine table (K values)
        self.K = [int(abs(math.sin(i + 1)) * 2**32) & 0xFFFFFFFF for i in range(64)]

        # Shift amounts for each round
        self.shifts = [
            7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
            5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
            4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
            6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21
        ]

    def _left_rotate(self, x, amount):
        """Left rotate a 32-bit integer"""
        x &= 0xFFFFFFFF
        return ((x << amount) | (x >> (32 - amount))) & 0xFFFFFFFF

    def _pad_message(self, message):
        """Pad message to be multiple of 512 bits"""
        msg_len = len(message)
        message += b'\x80'  # Append bit '1' followed by zeros

        # Pad with zeros until length ≡ 448 (mod 512)
        while len(message) % 64 != 56:
            message += b'\x00'

        # Append original length in bits as 64-bit little-endian
        message += struct.pack('<Q', msg_len * 8)
        return message

    def _process_chunk(self, chunk, A, B, C, D):
        """Process a 512-bit chunk"""
        # Break chunk into 16 32-bit words (little-endian)
        M = list(struct.unpack('<16I', chunk))

        # Initialize working variables
        a, b, c, d = A, B, C, D

        # Main loop - 64 operations in 4 rounds
        for i in range(64):
            if i < 16:
                # Round 1: F(b, c, d) = (b & c) | (~b & d)
                f = (b & c) | (~b & d)
                g = i
            elif i < 32:
                # Round 2: G(b, c, d) = (b & d) | (c & ~d)
                f = (b & d) | (c & ~d)
                g = (5 * i + 1) % 16
            elif i < 48:
                # Round 3: H(b, c, d) = b ^ c ^ d
                f = b ^ c ^ d
                g = (3 * i + 5) % 16
            else:
                # Round 4: I(b, c, d) = c ^ (b | ~d)
                f = c ^ (b | ~d)
                g = (7 * i) % 16

            f = (f + a + self.K[i] + M[g]) & 0xFFFFFFFF
            a, b, c, d = d, (b + self._left_rotate(f, self.shifts[i])) & 0xFFFFFFFF, b, c

        # Add chunk's hash to result
        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D = (D + d) & 0xFFFFFFFF

        return A, B, C, D

    def hash(self, message):
        """Compute MD5 hash of message"""
        if isinstance(message, str):
            message = message.encode('utf-8')

        # Pad the message
        padded = self._pad_message(message)

        # Initialize hash values
        A, B, C, D = self.A, self.B, self.C, self.D

        # Process each 512-bit chunk
        for i in range(0, len(padded), 64):
            chunk = padded[i:i+64]
            A, B, C, D = self._process_chunk(chunk, A, B, C, D)

        # Produce final hash (little-endian)
        return struct.pack('<4I', A, B, C, D).hex()


def main():
    """Main function to handle command-line usage like md5sum"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Compute MD5 hash (educational implementation)')
    parser.add_argument('files', nargs='*', help='Files to hash (stdin if not provided)')
    parser.add_argument('-c', '--check', action='store_true', help='Read MD5 sums from files and check them')
    parser.add_argument('-t', '--text', action='store_true', help='Read in text mode (default)')
    parser.add_argument('-b', '--binary', action='store_true', help='Read in binary mode')
    parser.add_argument('--demo', action='store_true', help='Run demonstration mode')

    args = parser.parse_args()
    md5 = MD5()

    # Demo mode
    if args.demo:
        test_strings = [
            "",
            "a",
            "abc",
            "message digest",
            "The quick brown fox jumps over the lazy dog"
        ]

        print("MD5 Hash Demonstration\n" + "="*60)
        for s in test_strings:
            hash_result = md5.hash(s)
            print(f"Input: '{s}'")
            print(f"MD5:   {hash_result}\n")

        print("="*60)
        print("Internal steps for 'abc':")
        print(f"Original message: abc")
        msg = b'abc'
        padded = md5._pad_message(msg)
        print(f"Padded length: {len(padded)} bytes ({len(padded)*8} bits)")
        print(f"Padded (hex): {padded.hex()}")
        print(f"Final hash: {md5.hash('abc')}")
        return

    # Read from stdin if no files provided
    if not args.files:
        data = sys.stdin.buffer.read()
        hash_result = md5.hash(data)
        print(f"{hash_result}  -")
    else:
        # Process each file
        for filename in args.files:
            try:
                mode = 'rb' if args.binary else 'rb'
                with open(filename, mode) as f:
                    data = f.read()
                hash_result = md5.hash(data)
                print(f"{hash_result}  {filename}")
            except FileNotFoundError:
                print(f"md5sum: {filename}: No such file or directory", file=sys.stderr)
            except PermissionError:
                print(f"md5sum: {filename}: Permission denied", file=sys.stderr)
            except Exception as e:
                print(f"md5sum: {filename}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
