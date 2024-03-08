# xmplibdump

Python utility to dump an [XMPlay](https://www.un4seen.com) media library to standard output in CSV format. Any standard CSV tool can then be used to parse the file and run statistics, look for amusing comments embeded in track metadata, and so on.

Generally speaking, any information you would see about a track via the media library pane or the `Track info` right-click menu will be dumped. Please refer to the [XMPlay library file format specification](https://support.xmplay.com/article.php?id=101) for more details on what is included. The resulting CSV will be UTF-8 encoded with fields separated by a comma and records separated by your operating system's default line-ending. Strings will be enclosed in double quotes.

## Prerequisites

- Python 3.x

## Usage

Dump a library to library.csv

    $ python xmplibdump.py xmplay.library > library.csv

View a library's metadata

    $ python xmplibdump.py --meta xmplay.library

