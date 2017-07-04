#!/usr/bin/env python

import argparse
from stf.lib.STFParser import STFParser

def main():
    """main function
    eg:
    PYTHONPATH=src python tools/ParserIniFile.py --iniFile config_file.ini --section Pipeline --option Build"""
    parser = argparse.ArgumentParser(description="parser INI file")
    parser.add_argument("--iniFile",
                        help="the full path of the ini file wihch will be parsered (required)",
                        required=True)
    parser.add_argument("--section",
                        help="the string of the section name (required)",
                        required=True)
    parser.add_argument("--option",
                        help="the string of the option name (required)",
                        required=True)
    args = parser.parse_args()
    iniFile = args.iniFile
    section = args.section
    option = args.option
    stfParser = STFParser(iniFile)
    value = stfParser.get(section, option)
    print value,
        

if __name__ == '__main__':
    main()