#!/usr/bin/env python3

from sys import argv, stdout
from serial import Serial
from binascii import hexlify, unhexlify
from time import sleep
from ast import literal_eval

from argparse import ArgumentParser
from logging  import getLogger, StreamHandler
from logging  import ERROR, WARNING, INFO, DEBUG, NOTSET

CHUNK_SIZE = 64*2

def parse_arguments():
    parser = ArgumentParser(description='Tool to assign MPNs to symbols in a KiCAD schematic')
    verbose = parser.add_mutually_exclusive_group()
    operation = parser.add_mutually_exclusive_group()
    verbose.add_argument(  "-q", "--quiet",    action = "store_true",                help = "turn off warnings")
    verbose.add_argument(  "-v",               action = "count",                     help = "set loglevel")
    parser.add_argument(   "-p", "--port",     type = str, default = "/dev/ttyUSB0", help = "path serial device")
    parser.add_argument(   "-b", "--baud",     type = int, default = 115200,         help = "baud rate")
    operation.add_argument("-u", "--upload",   type = str,                           help = "file to upload to MicroPython device")
    operation.add_argument("-d", "--download", type = str,                           help = "file to download from MicroPython device")
    operation.add_argument("-r", "--remove",   type = str,                           help = "file or directory to remove on MicroPython device")
    operation.add_argument("-l", "--list",     type = str,                           help = "file or directory to list contents of")
    operation.add_argument("-m", "--mkdir",    type = str,                           help = "path of directory to create on MicroPython device")
    parser.add_argument(   "-o", "--override", action = "store_true",                help = "override files and create necessary direcotries on MicroPython device")
    parser.add_argument(   "-f", "--file",     type = str, default = "",             help = "path to file on local filesystem")
    args = parser.parse_args()
    return args

def generate_logger(verbose, quiet):
    logger = getLogger()
    logger.addHandler(StreamHandler())
    if verbose:
        if   1 == verbose:
            logger.setLevel(INFO)
            logger.info("Verbose output.")
        elif 2 <= verbose:
            logger.setLevel(DEBUG)
            logger.debug("Debug output.")
    elif quiet:
        logger.setLevel(ERROR)
    return logger

def open_upy(port, baud):
    log.debug("Entering")
    log.info("Opening port and resetting ESP into run mode.")
    upy = Serial(port, baud)
    upy.reset_input_buffer()
    upy.rts=1
    upy.dtr=0
    upy.rts=0
    log.info("Sending ^c after 500ms.")
    sleep(0.5)
    upy.write(b'\x03')
    upy.flush()
    log.debug(upy.read_until(b'>>> ').decode("utf-8", errors='ignore'))
    sleep(0.01)
    if upy.in_waiting:
        log.debug(upy.read_until(b'>>> ').decode("utf-8", errors='ignore'))
    return upy

def command(upy, cmd):
    upy.write(cmd.encode("utf-8")+b'\r\n')
    upy.flush()
    result = upy.read_until(b'>>> ').decode("utf-8", errors='ignore')
    log.debug(result)
    return result[len(cmd)+2:-6]

def upload(upy, path, file):
    stat = command(upy, "'f' if stat(\"%s\")[0] is 0x8000 else 'd'" % path)
    if stat == "'d'":
        raise OSError("[Errno 17] EEXIST on MicroPython device")
    dir_path = "/" + "/".join(path.split("/")[:-1])
    mkdir(upy, dir_path)
    with open(file, "rb") as src:
        command(upy, "from ubinascii import unhexlify")
        command(upy, "des = open(\"%s\", \"wb\")" % path)
        hex_str = hexlify(src.read()).decode("utf-8")
        for i in range(0, len(hex_str), CHUNK_SIZE):
            command(upy, "des.write(unhexlify(b'%s'))" % hex_str[i:i+CHUNK_SIZE])
        command(upy, "des.close()")
    pass

def download(upy, path, file):
    stat = command(upy, "'f' if stat(\"%s\")[0] is 0x8000 else 'd'" % path)
    if "OSError: [Errno 2] ENOENT" in stat:
        raise OSError("[Errno 2] No such file or directory on MicroPython device")
    if stat == "'d'":
        raise OSError("Path is a directory")
    command(upy, "from ubinascii import hexlify")
    # hex_str = literal_eval(command(upy, "hexlify(open(\"%s\", \"rb\").read()).decode(\"utf-8\")" % path))
    hex_str = literal_eval(command(upy, "hexlify(open(\"%s\", \"rb\").read())" % path))
    with open(file, "wb") as des:
        des.write(unhexlify(hex_str))

def remove(upy, path):
    path_is_file = literal_eval(command(upy, "stat(\"%s\")[0] is 0x8000" % path))
    if path_is_file:
        # delete file
        command(upy, "remove(\"%s\")" % path)
    else:
        # delete recursively
        for node in listdir(upy, path):
            remove(upy, path+"/"+node)
        command(upy, "rmdir(\"%s\")" % path)

def listdir(upy, path):
    listing = command(upy, "listdir(\"%s\")" % path)
    if "OSError: [Errno 2] ENOENT" in listing:
        raise OSError("[Errno 2] No such file or directory on MicroPython device")
    return literal_eval(listing)

def mkdir(upy, path):
    subpaths = path.split("/")
    # remove leading /
    subpaths = [item for item in subpaths if item != '']
    full_path = ""
    for subpath in subpaths:
        full_path += "/" + subpath
        stat = command(upy, "'f' if stat(\"%s\")[0] is 0x8000 else 'd'" % full_path)
        if stat == "'d'":
            # existst already
            continue
        if "OSError: [Errno 2] ENOENT" in stat:
            # does not exist yes
            command(upy, "mkdir(\"%s\")" % full_path)
        if stat == "'f'":
            raise OSError("[Errno 17] EEXIST on MicroPython device")
    pass

if __name__ == "__main__":
    global log
    args = parse_arguments()
    log = generate_logger(args.v, args.quiet)
    with open_upy(args.port, args.baud) as upy:
        command(upy, "from os import listdir, mkdir, rmdir, remove, ilistdir, stat")
        if args.upload:
            upload(upy, args.upload, args.file)
        if args.download:
            download(upy, args.download, args.file)
        if args.remove:
            remove(upy, args.remove)
        if args.list:
            print("\n".join(listdir(upy, args.list)))
        if args.mkdir:
            mkdir(upy, args.mkdir)
