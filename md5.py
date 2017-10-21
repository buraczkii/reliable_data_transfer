import hashlib
import sys


if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('Usage: python md5 file_name')
    sys.exit(1)

  md5 = hashlib.md5()
  with open(sys.argv[1], 'r') as f:
    while True:
      block = f.read(1024)
      if not block: break
      md5.update(str.encode(block))
  print(repr(md5.digest()))
