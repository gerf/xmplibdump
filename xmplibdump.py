import sys
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description="Python utility to dump an XMPlay media library to standard output in CSV format.")

parser.add_argument('--meta', action='store_true', help='show library metadata only')
parser.add_argument('library', type=argparse.FileType('rb'), help='an XMPlay library file')
args = parser.parse_args()

library = args.library

def readString(handle):
    # sequentially read until null terminator (\x00)
    # double-quotes are escaped, and if the string is not null then it's wrapped in double-quotes
    s = ""
    while True:
        b = handle.read(1)
        if b == b'\x00' or len(b) == 0:
            break
        s = s + b.decode('utf-8', 'ignore')
    s = s.replace('"', '""')
    if len(s) > 0:
        s = '"' + s + '"'
    return s

def readInt(handle):
    # read a one-byte integer
    i = handle.read(1)
    return int.from_bytes(i)

def readDword(handle):
    # read a DWORD (bytes are in reverse order)
    n4 = handle.read(1)
    n3 = handle.read(1)
    n2 = handle.read(1)
    n1 = handle.read(1)
    return int.from_bytes(n1+n2+n3+n4)

def readWord(handle):
    # read a WORD (bytes are in reverse order)
    n2 = handle.read(1)
    n1 = handle.read(1)
    return int.from_bytes(n1+n2)

def readTimestamp(handle):
    # a timestamp-formatted DWORD
    # if zero, return an empty string instead
    d = readDword(handle)
    return datetime.fromtimestamp(d) if d > 0 else ""

def readFiletime(handle):
    # a Windows FILETIME-style timestamp
    # the math at the end is needed to convert between Windows and UNIX formats
    n8 = handle.read(1)
    n7 = handle.read(1)
    n6 = handle.read(1)
    n5 = handle.read(1)
    n4 = handle.read(1)
    n3 = handle.read(1)
    n2 = handle.read(1)
    n1 = handle.read(1)
    ticks = int.from_bytes(n1+n2+n3+n4+n5+n6+n7+n8)
    return datetime.fromtimestamp(ticks / 10000000 - 11644473600)

# refer to https://support.xmplay.com/article.php?id=101 for XMPlay library file format

# read header info
library_version = readInt(library)
zero1 = readInt(library)
zero2 = readInt(library)

if library_version == 0 or zero1 + zero2 > 0:
    sys.exit("Unexpected header format; is this a valid XMPlay library?")

# currently, the only "info flag" set is whether the library is UTF-8 or ASCII
info_flags = readInt(library)
encoding = 'utf-8' if info_flags & 0b10000000 > 0 else 'ascii'

# note the order is expected to be preserved (Python 3.7+ behavior) 
trackdata = {
        'file_name': readString,
        'track_title': readString,
        'title': readString,
        'artist': readString,
        'album': readString,
        'year': readString,
        'track': readString,
        'genre': readString,
        'comment': readString,
        'file_type': readString,
        'subsongs': readInt,
        'duration': readDword,
        'last_play': readTimestamp,
        'file_size': readDword,
        'play_count': readDword,
        'date_added': readTimestamp,
        'flags': readInt,
        'rating': readInt,
        'subsong_count': readWord,
        'subsong_number': readWord
        }

fields = trackdata.keys()

# output header if dumping the database
if not args.meta:
    print(','.join(fields))

entries = True

# output data until the end of the track listing is reached
while entries:
    subsongs = 1

    for field in fields:
        
        data = ''

        # subsong data only exist if there are subsongs, so we may need to skip fields
        if subsongs > 0 or (field != 'subsong_count' and field != 'subsong_number'):
            # execute the reading function specified for this field
            data = trackdata[field](library)

        # special case: the track data block end on a null filename
        if field == 'file_name' and len(data) == 0:
            entries = False;
            break

        # adjust subsongs flag when we get to it
        if field == 'subsongs':
            data = 1 if data > 0 else 0
            subsongs = data

        # finally, print out the data (unless we're in metadata mode)
        if not args.meta:
            print(data, end = '')

            # add a field separator as long as we're not on the last field
            if field != 'subsong_number':
                print(",", end = '')

    # end for loop (all fields have been processed for this track)
    if entries and not args.meta:
        print()

# end while loop (all tracks have been processed)

# output library metadata
if args.meta:
    print(f"Library version: {library_version}")
    print(f"Encoding: {encoding}")

    while True:
        watchdir = readString(library)
        
        if len(watchdir) == 0:
            break

        subfolders = "with" if readInt(library) == 2 else "without"
        updated = readFiletime(library)

        print(f"Watch directory: {watchdir} ({subfolders} subfolders, last updated {updated})")

# pack up and go home
library.close()
sys.exit(0)

