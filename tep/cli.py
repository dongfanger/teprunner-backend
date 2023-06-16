#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  7/17/2020 3:49 PM
@Desc    :  命令行
"""

import argparse
import sys

from tep import __description__, __version__
from tep.scaffold import init_parser_scaffold, main_scaffold


def main():
    # 命令行处理程序入口
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("-V", "--version", dest="version", action="store_true", help="show version")
    subparsers = parser.add_subparsers(help="sub-command help")
    sub_parser_scaffold = init_parser_scaffold(subparsers)

    if len(sys.argv) == 1:
        # tep
        parser.print_help()
        sys.exit(0)
    elif len(sys.argv) == 2:
        if sys.argv[1] in ["-V", "--version"]:
            # tep -V
            # tep --version
            print(f"{__version__}")
        elif sys.argv[1] in ["-h", "--help"]:
            # tep -h
            # tep --help
            parser.print_help()
        elif sys.argv[1] == "startproject":
            # tep startproject
            sub_parser_scaffold.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.version:
        print(f"{__version__}")
        sys.exit(0)

    if sys.argv[1] == "startproject":
        # tep startproject project_name
        main_scaffold(args)
