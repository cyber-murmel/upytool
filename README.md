# uPyTool

A better tool to up- and download files to and from [micropython]( https://micropython.org/).

## Usage
```
usage: upytool.py [-h] [-q | -v] [-p PORT] [-b BAUD]
                  [-u UPLOAD | -d DOWNLOAD | -r REMOVE | -l LIST | -m MKDIR]
                  [-f FILE]

Tool to up- and download files to and from micropython.

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           turn off warnings
  -v                    set verbose loglevel
  -p PORT, --port PORT  path serial device (default = "/dev/ttyUSB0")
  -b BAUD, --baud BAUD  baud rate (default = 115200)
  -u UPLOAD, --upload UPLOAD
                        path on MicroPython device where the uploaded file
                        shall be saved
  -d DOWNLOAD, --download DOWNLOAD
                        path on MicroPython device of file to be downloaded
  -r REMOVE, --remove REMOVE
                        path on MicroPython device of file or directory to be
                        deleted
  -l LIST, --list LIST  path on MicroPython device of directory to list
                        contents of
  -m MKDIR, --mkdir MKDIR
                        path on MicroPython device of directory to be created
  -f FILE, --file FILE  path on local filesystem of file to be uploaded from
                        or downloaded to
```

## Examples

### Delete Everything on MicroPython Device
```
./upytool.py -r /
```

### Upload File to  MicroPython Device
This works even without the directory `/wifi_tk` being present on the device.
The Directory will be automatically created.  
```
./upytool.py -f sta_conf_arr.json -u /wifi_tk/sta_conf_arr.json
```

### Upload Entire Project Directory to MicroPython Device
`cd` into project directory.

` ~/curr/Software\ Proejcts/upytool/upytool.py` is the path of the script on my machine.
```
for f in `find ./ -type f`; { ~/curr/Software\ Proejcts/upytool/upytool.py -u ${f:1} -f $f }
```
