
import os
import argparse


def get_bytes_nice(bytes):
    bytes_nice = bytes
    unit_nice = 'B'
    if bytes < (1024 << 10):
        bytes_nice = bytes / 1024
        unit_nice = 'KiB'
    elif bytes < (1024 << 20):
        bytes_nice = bytes / (1024 << 10)
        unit_nice = 'MiB'
    elif bytes < (1024 << 30):
        bytes_nice = bytes / (1024 << 20)
        unit_nice = 'GiB'
    elif bytes < (1024 << 40):
        bytes_nice = bytes / (1024 << 30)
        unit_nice = 'TiB'
    return bytes_nice, unit_nice


def frac_type(arg):
    val = float(arg)
    if not 0 < val < 1:
        raise argparse.ArgumentTypeError('expected a fraction arg in (0,1)')
    return val


def unsigned_int(arg):
    arg = int(arg)
    if arg < 0:
        raise argparse.ArgumentError('Argument must be a nonnegative integer')
    return arg


def positive_int(arg):
    arg = int(arg)
    if arg <= 0:
        raise argparse.ArgumentError('Argument must be a positive integer')
    return arg


def prettyprint_args(ns):
    print(os.linesep + 'Input arguments -- ')
    
    for k,v in ns.__dict__.items():
        print('{}: {}'.format(k,v))

    print()
    return
