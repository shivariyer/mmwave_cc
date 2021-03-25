
import os
import argparse


def get_bytes_nice(bytes, kibi=False):
    bytes_nice = bytes
    kilo = 1024 if kibi else 1000
    unit_nice = 'B'
    if kibi:
        if bytes < (kilo << 10):
            bytes_nice = bytes / kilo
            unit_nice = 'KiB'
        elif bytes < (kilo << 20):
            bytes_nice = bytes / (kilo << 10)
            unit_nice = 'MiB'
        elif bytes < (kilo << 30):
            bytes_nice = bytes / (kilo << 20)
            unit_nice = 'GiB'
        elif bytes < (kilo << 40):
            bytes_nice = bytes / (kilo << 30)
            unit_nice = 'TiB'
    else:
        if bytes < kilo**2:
            bytes_nice = bytes / kilo
            unit_nice = 'KB'
        elif bytes < kilo**3:
            bytes_nice = bytes / (kilo**2)
            unit_nice = 'MB'
        elif bytes < kilo**4:
            bytes_nice = bytes / (kilo**3)
            unit_nice = 'GB'
        elif bytes < kilo**5:
            bytes_nice = bytes / (kilo**4)
            unit_nice = 'TB'
        
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
