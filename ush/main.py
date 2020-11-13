#!/usr/bin/env python

"""
File Name   : main.py
Description : NSEM main program - for managability main redirects subprocesses into their respective function
Usage       : conda activate A_PYTHON_ENV and then python main -h to see the usage per subprocess
Date        : 7/6/2020
Contacts    : Coastal Act Team 
              ali.abdolali@noaa.gov, saeed.moghimi@noaa.gov, beheen.m.trimble@gmail.com, andre.vanderwesthuysen@noaa.gov
"""

# standard libs
import  os, sys
import argparse

# local libs
import func_nsem_build    as fbn
import func_nsem_prep     as fnp
import func_nsem_workflow as fnw
import nsem_utils         as nus



if __name__ == '__main__':

    usage = "%s --help | -h \n"  %sys.argv[0]
    print(nus.colory("red",usage))
   

    parser = argparse.ArgumentParser()
    subp = parser.add_subparsers()
   
    nco = subp.add_parser("workflow", help="reads an initialization file and construct the NSEM workflow")
    nco.add_argument("--ini", help="an init python file with prepopulated values", default="nsem_ini.py")
    nco.set_defaults(func=fnw.nsem_workflow)
    

    build_install = subp.add_parser("build", help="buils and installs NSEM models with NEMS")
    build_install.add_argument("--ini", help="an init python file with prepopulated values", default="nsem_ini.py")
    build_install.set_defaults(func=fbn.nsem_build)
  

    prep_data = subp.add_parser("prep", help="prepares NSEM models input files")
    prep_data.add_argument("--ini", help="an init python file with prepopulated values", default="nsem_ini.py")
    prep_data.add_argument("--nwm", action='store_true', help="prepares data for the NWM")
    prep_data.add_argument("--adc", action='store_true', help="prepares data for the ADCIRC")
    prep_data.add_argument("--ww3", action='store_true', help="prepares data for the WW3")
    prep_data.add_argument("--atmesh", action='store_true', help="prepares data for the ATMesh")
    prep_data.add_argument("--atm", action='store_true', help="prepares data for the ATM")
    prep_data.add_argument("--ww3data", action='store_true', help="prepares data for the WW3Data")
    prep_data.set_defaults(func=fnp.nsem_prep)
  

    args = parser.parse_args()
    print(args)
    args.func(args)

