"""
File Name   : nsem_utils.py
Description : NSEM utility file - more generic functions used by other files
Usage       : import this into an external python source file (i.e. import nsem_utils as utils) 
Date        : 7/6/2020
Contacts    : Coastal Act Team 
              ali.abdolali@noaa.gov, saeed.moghimi@noaa.gov, beheen.m.trimble@gmail.com, andre.vanderwesthuysen@noaa.gov
"""

from string import Template
import datetime, time
import argparse, os, sys


# local libs
from color import Color, Formatting, Base, ANSI_Compatible


def colory(which, text):
     msg = ""
     if which.lower() == "red" :
         msg = Color.F_Red + text
     elif which.lower() == "green" :
         msg = Color.F_Green + text
     elif which.lower() == "blue" :
         msg = Color.F_Blue + text
     msg += Color.F_Default
     return msg



def now(frmt=1):

    now = datetime.datetime.now()

    if frmt == 1:
        now = now.strftime("%Y-%m-%d %H:%M:%S")
    elif frmt == 2:
        now = now.strftime("%b. %d, %Y")
    elif frmt == 3:
        now = now.ctime()
    elif frmt == 4:
        now = now.strftime("%Y%m%d")

    return now



def dateloop_byday(start_date, duration_days):

    for n in range(duration_days):
        yield start_date + datetime.timedelta(days=n)



def dateloop_byhour(start_date, duration_hours):

    for n in range(duration_hours):
        yield start_date + datetime.timedelta(hours=n)



def dateloop_15min(start_date, duration_min):

    min_cntr = 0
    for n in range(duration_min):
        if min_cntr == 15:
            min_cntr = 0
            yield start_date + datetime.timedelta(minutes=n)
        min_cntr += 1



# TODO - test this
def to_date(date_str,frmt=3):

    if frmt == 1:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    elif frmt == 2:
        return datetime.datetime.strptime(date_str, "%b. %d, %Y")
    elif frmt == 3:
        return datetime.datetime.strptime(date_str).ctime()
    elif frmt == 4:
        return datetime.datetime.strptime(date_str, "%Y%m%d")
    elif frmt == 5:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')


def exist(path):
    p = os.path.abspath(path)
    if os.path.isdir(p):
        return 1
    return 0


def found(file):

    f = os.path.abspath(file)
    if not os.path.isfile(f):
        print(colory("red", "\nFile {} not found!".format(file)))
        return 0
    return 1


def import_file(filename):

    directory, module_name = os.path.split(filename)
    module_name = os.path.splitext(module_name)[0]

    path = list(sys.path)
    sys.path.insert(0, directory)

    try:
        module = __import__(module_name)
        return module
    finally:
        sys.path[:] = path # restore



def tmp2scr(filename=None,tmpname=None,d=None):
    """
    Replace a pattern in tempelate file and generate a new input file.
    filename: full path to input file
    tmpname:  full path to tempelate file
    d:        dictionary of all patterns need to replace   

    Uses string.Template from the Python standard library
    """
    fileout = open( filename,'w' )
    filetmp = open( tmpname ,'r' )
    out = Template( filetmp.read() ).safe_substitute(d)
    fileout.write(str(out))
    fileout.close()
    filetmp.close()
    return out   # just-incase if needed 


def replace_pattern_line(filename, pattern, line2replace):
    """
    replace the whole line if the pattern found
    
    """

    tmpfile = filename+'.tmp2'
    os.system(' cp  -f ' + filename + '  ' + tmpfile)
    tmp  = open(tmpfile,'r')
    fil  = open(filename,'w')
    for line in tmp:
        fil.write(line2replace if pattern in line else line)

    tmp.close()
    fil.close()
    os.system('rm ' + tmpfile  )


class BlankLinesHelpFormatter (argparse.HelpFormatter):
    # add empty line if help lines ends with \n
    # default with=54
    def _split_lines(self, text, width):

        # default _split_lines removes final \n and reduces all interior whitespace to one blank
        lines = super()._split_lines(text, width)
        if text.endswith('\n'):
            lines += ['']
        return lines

