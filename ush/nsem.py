#!/usr/bin/env python


# standard libs
import glob, os, sys, re, time
import argparse
import functools, operator 
import datetime, subprocess
from importlib import import_module
from pathlib import Path
import shutil

# local libs
from color import Color, Formatting, Base, ANSI_Compatible

# globals - updated during reading command line
PRJ_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
RUN_DIR = os.path.dirname(os.path.abspath(__file__))


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


def exist(path):
    p = os.path.abspath(path)
    if os.path.isdir(p):
        return 1
    return 0


def found(file):

    f = os.path.abspath(file)
    if not os.path.isfile(f):
        msg = Color.F_Red + "\nFile {} not found!".format(file)
        msg += Color.F_Default
        print(msg)
        return 0
    return 1




# ecflow nco variables:
# **********************
# envir Set to "test" during the initial testing phase, "para" when running in parallel (on a schedule), and "prod" in production.
# COMROOT com root directory for input/output data on current system ecFlow $COMROOT/$NET/$envir/$RUN.$PDY
# NWROOT Root directory for application, typically /nw$envir
# GESROOT nwges root directory for input/output guess fields on current system
# job Unique job name (unique per day and environment)
# jobid Unique job identifier, typically $job.$$ (where $$ is an ID number)
# jlogfile Log file for start time, end time, and error messages of all jobs
# cyc Cycle time in GMT, formatted HH
# DATAROOT Directory containing the working directory, often /tmpnwprd1 in production
# HOMEmodel Application home directory, typically $NWROOT/ model.v X . Y . Z
# SENDWEB Boolean variable used to control sending products to a web server, often ncorzdm
# KEEPDATA Boolean variable used to specify whether or not the working directory should be deleted upon successful job completion.

# model_ver Current version of the model; where model is the model's directory name (e.g. for $NWROOT/gfs.v12.0.0, gfs_ver=v12.0.0)
# jjob nco variables:
# *******************
# pgmout File where stdout of binary executables may be written
# NET Model name (first level of com directory structure)
# RUN Name of model run (third level of com directory structure)
# PDY Date in YYYYMMDD format
# PDYm1-7 Dates of previous seven days in YYYYMMDD format ($PDYm1 is yesterday's date, etc.)
# PDYp1-7 Dates of next seven days in YYYYMMDD format ($PDYp1 is tomorrow's date, etc.)
# cycle Cycle time in GMT, formatted tHHz
# DATA Location of the job working directory, typically $DATAROOT/$jobid
# USHmodel Location of the model's ush files, typically $HOME model /ush
# EXECmodel Location of the model's exec files, typically $HOME model /exec
# PARMmodel Location of the model's parm files, typically $HOME model /parm
# FIXmodel Location of the model's fix files, typically $HOME model /fix
# COMIN com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
# COMOUT com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
# COMINmodel com directory for incoming data from model model
# COMOUTmodel com directory for outgoing data for model model
# GESIN nwges directory for input guess fields; typically $GESROOT/$envir
# GESOUT nwges directory for output guess fields; typically $GESROOT/$envir

# Each job in ecFlow is associated with an ecFlow script which acts like an LSF submission script,
# 1) setting up the bsub parameters and much of
# 2) the execution environment and
# 3) calling the J-job to execute the job.
# 4) All jobs must be submitted to LSF via bsub .
# 5) It is at the ecFlow (NCO) or submission script level (development organizations) where certain
#    environment specific variables must be set

# The purpose of the J-Job is fourfold:
# 1) to set up location (application/data directory) variables,
# 2) to set up temporal (date/cycle) variables,
# 3) to initialize the data and working directories,
# 4) and to call the ex-script.

# The ex-script is the driver for the bulk of the application,
# 1) including data-staging in the working directory,
# 2) setting up any model-specific variables,
# 3) moving data to long-term storage,
# 4) sending products off WCOSS via DBNet and
# 5) performing appropriate validation and error checking.
# 6) It may call one or more utility (ush) scripts.
class NCOSystem():

    SCRIPT = 'scripts'
    SOURCE = 'sorc'
    ECF = 'ecf'
    USH = 'ush'
    EXEC = 'exec'
    PARM = 'parm'
    FIX = 'fix'
    JOBS = 'jobs'

    # unique run_dir is constructed by this format - Note: currenty RUN_DIR includes the nsem

    """ $COMROOT/$NET/$envir/$RUN.$PDY
        COMIN com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        COMOUT com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        COMINmodel com directory for incoming data from model model

    <RUN_DIR>/                                              ==> ${COMROOT}/
        |--- nsem                                           ==> $NET - first level dir
                |--- $envir/                                ==> test|para|prod
                        |--- logs
                        |     |--- j<logfile>jobid          ==> j$job$$
                        |--- <storm>/                       ==> this is extra in the hi-er-archy
                               |--- <input_data>            ==> $COMIN
                               |
                               |
                               |--- <run_name>/             ==> $RUN - third level dir
                                        |--- <out_data>/    ==> $COMOUT

                                                            (i.e. $COMROOT/$NET/$envir/$RUN.$PDY
    'COMROOT' : RUN_DIR,     # let's call this run_dir
    'GESROOT' : GESROOT,     # let's have this in comroot/nwges
    'DATAROOT': DATAROOT,    # let's mak this on /tmp<storm>|/tmp<nsem>
    'NWROOT'  : PRJ_DIR      # let's call this prj_dir

    """

    def __init__(self, event, envir, run_name, dataroot, gesroot, model="nsem"):

        self.COMROOT = RUN_DIR               # COMROOT root directory for input/output data on current system
        self.GESROOT = gesroot               # GESROOT nwges root directory for input/output guess fields on current system
        self.DATAROOT = dataroot             # DATAROOT Directory containing the working directory, often /tmpnwprd1 in production
        self.NWROOT = PRJ_DIR                # NWROOT Root directory for application, typically /nw$envir
        self.NET = event.lower()
        self.envir = envir.lower()
        self.RUN = run_name.lower()
        self.job = self.RUN                  # job Unique job name (unique per day and environment)


        self.jlogfile = os.path.join(self.COMROOT, self.envir, "logs", "jlogfile." + self.job)

        # com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        self.COMIN = os.path.join(self.COMROOT, self.envir, self.NET)
        self.COMINnwm = os.path.join(self.COMIN,"nwm")

        # com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        # see if needed, created in jjob too
        self.COMOUT = os.path.join(self.COMROOT, self.envir, self.NET, self.RUN)

        # GESIN nwges directory for input guess fields; typically $GESROOT/$envir
        self.GESIN = os.path.join(self.GESROOT, self.envir, "nwgs")

        # GESOUT nwges directory for output guess fields; typically $GESROOT/$envir TODO - see if needed, created in jjob script too
        #self.GESOUT = os.path.join(self.GESROOT, self.envir)

        # DATA Location of the job working directory, typically $DATAROOT/$jobid
        # This directory gets created though jjob script, I think make DATAROOT+=NET


    def write_helper(self, nems_cfg):

        # create a helper export variables

        nwroot = self.NWROOT

        lines="""#!/bin/sh -l

# To Run: source export_env.sh

# Enviroment vars from ecFlow scripting
export RUN_DIR={}
export NWROOT={}
export FIXnsem={}/fix
export EXECnsem={}/exec
export SORCnsem={}/sorc
export PARMnsem={}/parm
export USHnsem={}/ush
export GESIN={}
export COMIN={}
export COMINatm={}
export COMINwave={}
export COMINwavedata={}
export COMINmeshdata={}
export COMINadc={}
export COMINnwm={}
export STORM={}
export RUN_TYPE={}
export jlogfile={}
""".format(self.COMROOT,nwroot,nwroot,nwroot,nwroot,nwroot,nwroot,self.GESIN,self.COMIN,
           os.path.join(self.COMIN,"atm"), os.path.join(self.COMIN,"ww3"),
           os.path.join(self.COMIN,"ww3data"), os.path.join(self.COMIN,"atmesh"),
           os.path.join(self.COMIN,"adcirc"), self.COMINnwm,
           self.NET, self.RUN, self.jlogfile)

        outfile = os.path.join(self.ush_dir(), "nsem_export.sh")
        with open(outfile, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed helper export script %s" %outfile)

        start_date, start_date_str = nems_cfg.get_duration()

        lines= ["# To Use - import this into your python script as follow:",
                "# import nsem_env",
                "",
                "import sys, os",
                "",
                "",
                "RUNdir = os.getenv('RUNdir')",
                "PRJdir = os.getenv('NWROOT')",
                "EXECnsem = os.getenv('EXECnsem')",
                "PARMnsem = os.getenv('PARMnsem')",
                "FIXnsem = os.getenv('FIXnsem')",
                "USHnsem = os.getenv('USHnsem')",
                "GESIN = os.getenv('GESIN')",
                "COMIN = os.getenv('COMIN')",
                "COMINatm = os.getenv('COMINatm')",
                "COMINwave = os.getenv('COMINww3')",
                "COMINwavdata = os.getenv('COMINww3data')",
                "COMINadc = os.getenv('COMINadc')",
                "COMINnwm = os.getenv('COMINnwm')",
                "jlogfile = os.getenv('jlogfile')",
                "",
                "storm = os.getenv('STORM')",
                "run = os.getenv('RUN_TYPE')",
                "",
                'start_date_str = "' + start_date_str + '"',
                "frcst_hrs = " + str(nems_cfg.get_fcst_hours()),
                "",
                "if storm:",
                "    pass",
                "else:",
                '    print("\\nEnvironment is not set! Please source \'nsem_export.sh\' file and re run the program\\n")',
                "    sys.exit(-1)",
                "",
                "sys.path.append(USHnsem)",
                "",
                'print("\\n")',
                'print("Logfile: ' + self.jlogfile + '")',
                'print("\\n")',
                ""]

        outfile = os.path.join(self.ush_dir(), "nsem_env.py")
        with open(outfile, 'w') as fptr:
            fptr.write("\n".join(lines))

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed helper environment script %s" %outfile)


    def prj_dir(self):
        dir_iterable = [self.source_dir(), self.script_dir(), self.ecf_dir(), self.parm_dir(),
                        self.fix_dir(), self.ush_dir(), self.exec_dir(), self.jjob_dir()]
        # generator expression
        return (dir for dir in dir_iterable)

    """
    To test in python env:
    >>> get_genrator = self.prj_subdir()
    >>> get_generator
    <generator object prj_subdir at 0x7f78b2e7e2b0>
    >>> line = next(get_generator)
    .../parm/storms/<shinnecock>
    >>> line
    .../fix/meshes/<shinnecock>
    """
    def prj_subdir(self):
        # <prj_dir>/parm/storms/<event> - to exists
        # <prj_dir>/fix/template
        # <prj_dir>/fix/meshes/<event>
        # <prj_dir>/sorce/hsofs  hsofs_elevated20m ??
        subdir_iterable = [os.path.join(self.parm_dir(), "storms", self.NET),
                           os.path.join(self.fix_dir(), "meshes", self.NET),
                           os.path.join(self.fix_dir(), "templates")]
        for subdir in subdir_iterable:
            yield subdir


    def source_dir(self):
        return os.path.join(self.NWROOT, self.SOURCE)


    def script_dir(self):
        return os.path.join(self.NWROOT, self.SCRIPT)


    def ecf_dir(self):
        return os.path.join(self.NWROOT, self.ECF)


    def fix_dir(self):
        return os.path.join(self.NWROOT, self.FIX)


    def ush_dir(self):
        return os.path.join(self.NWROOT, self.USH)


    def exec_dir(self):
        return os.path.join(self.NWROOT, self.EXEC)


    def parm_dir(self):
        return os.path.join(self.NWROOT, self.PARM)


    def jjob_dir(self):
        return os.path.join(self.NWROOT, self.JOBS)


    def storm_dir(self, which):
        # running two storms even for testing overrides ecf/jjob files!
        # TODO - let them know about this case!!
        if which == "ecf":
            which = self.ecf_dir()
        elif which == "job":
            which = self.jjob_dir()

        p = os.path.join(which, self.NET)
        if not exist(p):
            print("\nCreating directory: {}".format(p))
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating directory: ', err)
        return p


    def setup_prjdir(self):
        # update the prj_dir for new storm event - TOO
        # <prj_dir>/parm/<event> - to exists
        # <prj_dir>/fix/meshes/<event>   hsofs  hsofs_elevated20m ??
        # <prj_dir>/sorc/runupforecast.fd ??
        p = self.NWROOT
        print("Checking health of project directory: {}".format(p))
        if not exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
                subprocess.check_call(['mkdir', '-v', self.SOURCE, self.SCRIPT, self.ECF, self.FIX,
                                       self.USH, self.EXEC, self.PARM, self.JOBS], cwd=p)
            except subprocess.CalledProcessError as err:
                print('Error in creating model home directory: ', err)
        else:
            for dir in self.prj_dir():
                if not exist(dir):
                    try:
                      subprocess.run(['mkdir', '-vp', dir ], check=True)
                    except subprocess.CalledProcessError as err:
                      print('Error in creating %s directory: ' %(dir, err))
                #else:
                #    print("\n%s is healthy" %dir)

        # now check on subdirs:
        for dir in self.prj_subdir():
            if not exist(dir):
                try:
                  subprocess.run(['mkdir', '-vp', dir ], check=True)
                except subprocess.CalledProcessError as err:
                  print('Error in creating %s directory: ' %(dir, err))
            #else:
            #    print("\n%s is healthy" %dir)


    # Run dir and subdir
    def run_subdir(self):
        subdir_iterable = ['nwm', 'adcirc', 'ww3', 'atmesh', 'atm']
        for subdir in subdir_iterable:
            yield subdir


    def setup_rundir(self):
        p = self.COMIN
        print("Checking health of run directory: {}".format(p))
        if not exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating model input directory: ', err)

        for dir in self.run_subdir():
            subdir = os.path.join(p, dir)
            if not exist(subdir):
                try:
                  subprocess.run(['mkdir', '-vp', subdir ], check=True)
                except subprocess.CalledProcessError as err:
                  print('Error in creating %s directory: ' %(subdir, err))


        """created on script side with id
        p = self.COMOUT
        if not exist(p):
            print("\nCreating model output directory: {}".format(p))
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating model input directory: ', err)
        """

        p = self.GESIN
        print("Checking restart directory: {}".format(p))
        if not exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating gesin directory: ', err)


        """created on script side with id
        p = self.GESOUT
        if not exist(p):
            print("\nCreating gesout directory: {}".format(p))
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating gesout directory: ', err)
        """

        # this is a dev logfile, so creating it here.
        # there is one also in ecf script to create, upon running!! One is extra!!
        p = self.jlogfile
        print("Checking logs directory: {}".format(p))
        if not exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating logs directory: ', err)


    def write_ecf2(self, slurm):

        sbatch_part = slurm.get_sbatch()

        lines = """\n\n#%include <head.h>
#%include <envir.h>

# base name of model directory (i.e. storm)
export model={}

# set to test during the initial testing phase, para when running
# in parallel (on a schedule), and prod in production
export envir={}

export DEVWCOSS_USER=$(whoami)

# models input/output location
export COMROOT={}

# models restart/spinup files location
export GESROOT={}

# root directory for application, typically /nw$envir
export NWROOT={}

# unique job name (unique per day and environment), run_name
export job=j{}
export jobid=$job.$$

# temp directory containing the working directory, often /tmpnwprd1 in production
export DATAROOT={}


# dev environment jlogfile
mkdir -p ${{COMROOT}}/${{envir}}/logs
export jlogfile=${{COMROOT}}/${{envir}}/logs/jlogfile.${{job}}

# call the jjob script
${{NWROOT}}/jobs/{}


#%manual
######################################################################
# Task script:     j{}
# Last modifier:   Andre van der Westhuysen
# Organization:    NOAA/NCEP/EMC/NOS/OWP
# Date:            {}
# Purpose: To execute the job for ADC-WW3-NWM model
######################################################################
######################################################################
# Job specific troubleshooting instructions:
# see generic troubleshoot manual page
#
######################################################################
#%end""".format(self.NET, self.envir, self.COMROOT, self.GESROOT,
                self.NWROOT, self.RUN, self.DATAROOT,
                "J"+self.RUN.upper(),
                self.RUN, now(2))

        outfile = os.path.join(self.ecf_dir(), "j"+self.RUN + ".ecf")
        # running two storms at once, even for testing, overrides ecf files
        # p = self.storm_dir("ecf")
        # outfile = os.path.join(p, "j"+self.RUN + ".ecf")
        with open(outfile, 'w') as fptr:
            fptr.write(sbatch_part+lines)

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed ecflow script %s" %outfile)



    def write_ecf(self, slurm):

        sbatch_part = slurm.get_sbatch()

        lines = """\n\n#%include <head.h>
#%include <envir.h>

# base name of model directory (i.e. storm)
export model={}

# set to test during the initial testing phase, para when running
# in parallel (on a schedule), and prod in production
export envir={}

export DEVWCOSS_USER=$(whoami)

# models input/output location
export COMROOT={}

# models restart/spinup files location
export GESROOT={}

# root directory for application, typically /nw$envir
export NWROOT={}

# unique job name (unique per day and environment), run_name
export job=j{}
export jobid=$job.$$

# temp directory containing the working directory, often /tmpnwprd1 in production
export DATAROOT={}

# log directory and files
mkdir -p {}
export jlogfile={}

# call the jjob script
{}


#%manual
######################################################################
# Task script:     j{}
# Last modifier:   Andre van der Westhuysen
# Organization:    NOAA/NCEP/EMC/NOS/OWP
# Date:            {}
# Purpose: To execute the job for ADC-WW3-NWM model
######################################################################
######################################################################
# Job specific troubleshooting instructions:
# see generic troubleshoot manual page
#
######################################################################
#%end""".format(self.NET, self.envir, self.COMROOT, self.GESROOT,
                self.NWROOT, self.RUN, self.DATAROOT,
                os.path.join(self.COMROOT, self.envir, "logs"),
                self.jlogfile,
                os.path.join(self.jjob_dir(),"J"+self.RUN.upper()),
                self.RUN, now(2))

        outfile = os.path.join(self.ecf_dir(), "j"+self.RUN + ".ecf")
        # running two storms at once, even for testing, overrides ecf files
        # p = self.storm_dir("ecf")
        # outfile = os.path.join(p, "j"+self.RUN + ".ecf")
        with open(outfile, 'w') as fptr:
            fptr.write(sbatch_part+lines)

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed ecflow script %s" %outfile)




    def write_jjob(self):

        lines="""#!/bin/sh

date
export PS4=' $SECONDS + '
set -x

export pgm="NWPS"
export pgmout=OUTPUT.$$

export KEEPDATA="YES"     # TODO - to see

PDY={}

# temp location of the job working directory, typically $DATAROOT/$jobid
export DATA=${{DATA:-${{DATAROOT:?}}/$jobid}}
mkdir -p $DATA
cd $DATA

####################################
# Specify NET and RUN Name and model
####################################
export NET={}
#export RUN=$(echo j{}|awk -F"_" '{{print $2}}')

####################################
# SENDECF  - Flag Events on ECFLOW
# SENDCOM  - Copy Files From TMPDIR to $COMOUT
# SENDDBN  - Issue DBNet Client Calls
####################################
export SENDCOM=${{SENDCOM:-YES}}
export SENDECF=${{SENDECF:-YES}}
export SENDDBN=${{SENDDBN:-NO}}

# Specify Execution Areas
####################################
export HOMEnsem={}
export FIXnsem={}
export EXECnsem={}
export SORCnsem={}
export PARMnsem={}
export USHnsem={}

# Set processing DIRs here
export INPUTdir=${{INPUTdir:-${{DATA}}/input}}
export RUNdir=${{RUNdir:-${{DATA}}/run}}
export TMPdir=${{TMPdir:-${{DATA}}/tmp}}
export LOGdir=${{LOGdir:-${{DATA}}/logs}}

# Set NWPS run conditions
export DEBUGGING=${{DEBUGGING:-TRUE}}
export DEBUG_LEVEL=${{DEBUG_LEVEL:-1}}
export ISPRODUCTION=${{ISPRODUCTION:-TRUE}}
export SITETYPE=${{SITETYPE:-EMC}}

##############################################
# Define COM directory
##############################################
# com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
export COMOUT={}
# nwges directory for output guess fields; typically $GESROOT/$envir
export GESOUT={}
# nwges directory for input guess fields; typically $GESROOT/$envir
export GESIN={}

# loop over nems.configure per model(alias), also must match run_name
# COMIN com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
# COMINmodel com directory for incoming data from model model
export COMINatm={}
export COMINwave={}
export COMINwavedata={}
export COMINadc={}
export COMINmeshdata={}
export COMINnwm={}

# check if we need to create COMOUT and GESOUT here or in main?
mkdir -p $INPUTdir $RUNdir $TMPdir $LOGdir $COMOUT $GESOUT
##############################################
# Execute the script
{}
##############################################

#startmsg
msg="JOB j{} HAS COMPLETED NORMALLY."
# postmsg $jlogfile "$msg"

if [ -e $pgmout ]; then
    cat $pgmout
fi

cd {}

if [ "$KEEPDATA" != YES ]; then
    rm -rf $DATA
fi

date

""".format(now(4), self.NET, self.job, self.NWROOT, self.fix_dir(), self.exec_dir(),
           self.source_dir(), self.parm_dir(), self.ush_dir(),
	   self.COMOUT, self.GESOUT, self.GESIN,
           os.path.join(self.COMIN,"atm"),
	   os.path.join(self.COMIN,"ww3"), os.path.join(self.COMIN,"ww3data"),
	   os.path.join(self.COMIN,"adcirc"), os.path.join(self.COMIN,"atmesh"),
	   os.path.join(self.COMIN,"nwm"), os.path.join(self.script_dir(),"ex"+self.RUN+".sh"),
           self.job, self.DATAROOT)

        outfile = os.path.join(self.jjob_dir(), "J"+self.RUN.upper())
        # running two storms at once, even for testing, overrides ecf files
        # p = self.storm_dir("job")
        # outfile = os.path.join(p, "J"+self.RUN.upper())
        with open(outfile, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed ecflow jjob script %s" %outfile)


        # create the script at the same time as jjob
        out = os.path.join(self.script_dir(),"ex"+self.RUN+".sh")

        # this script must exists that does the real work
        p = os.path.join(self.ush_dir(), self.RUN+".py")
        if not found(p):
            print("Warrning - make sure to prepare the script!")

        lines="""
echo "============================================================="
echo "=                                                            "
echo "=         RUNNING NSEM FOR STORM: {}
echo "=         RUN NAME: {}
echo "=                                                            "
echo "============================================================="
#
python ${{USHnsem}}/{}

echo "{} completed"
exit 0
""".format(self.NET, self.RUN, self.RUN+".py", self.RUN)

        with open(out, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", out])

        print("\nProcessed ecflow script %s" %out)



    def write_jjob2(self):

        lines="""#!/bin/sh

date
export PS4=' $SECONDS + '
set -x

export pgm="NWPS"
export pgmout=OUTPUT.$$

export KEEPDATA="YES"     # TODO - to see

PDY="$(date +'%Y%m%d')"

# temp location of the job working directory, typically $DATAROOT/$jobid
export DATA=${{DATA:-${{DATAROOT:?}}/$jobid}}
mkdir -p $DATA
cd $DATA

####################################
# Specify NET and RUN Name and model
####################################
export NET=${{model}}
#export RUN=$(echo ${{job}}|awk -F"_" '{{print $2}}')

####################################
# SENDECF  - Flag Events on ECFLOW
# SENDCOM  - Copy Files From TMPDIR to $COMOUT
# SENDDBN  - Issue DBNet Client Calls
####################################
export SENDCOM=${{SENDCOM:-YES}}
export SENDECF=${{SENDECF:-YES}}
export SENDDBN=${{SENDDBN:-NO}}

####################################
# Specify Execution Areas
####################################
export HOMEnsem=${{NWROOT}}
export FIXnsem=${{FIXnsem:-${{HOMEnsem}}/fix}}
export EXECnsem=${{EXECnsme:-${{HOMEnsem}}/exec}}
export SORCnsem=${{SORCnsem:-${{HOMEnsem}}/sorc}}
export PARMnsem=${{PARMnsem:-${{HOMEnsem}}/parm}}
export USHnsem=${{USHnsem:-${{HOMEnsem}}/ush}}

# Set processing DIRs here
export INPUTdir=${{INPUTdir:-${{DATA}}/input}}
export RUNdir=${{RUNdir:-${{DATA}}/run}}
export TMPdir=${{TMPdir:-${{DATA}}/tmp}}
export LOGdir=${{LOGdir:-${{DATA}}/logs}}

# Set NWPS run conditions
export DEBUGGING=${{DEBUGGING:-TRUE}}
export DEBUG_LEVEL=${{DEBUG_LEVEL:-1}}
export ISPRODUCTION=${{ISPRODUCTION:-TRUE}}
export SITETYPE=${{SITETYPE:-EMC}}

##############################################
# Define COM directory
##############################################
# com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
export COMOUT=${{COMROOT}}/${{envir}}/${{NET}}/${{job}}.${{PDY}}
# nwges directory for output guess fields; typically $GESROOT/$envir
export GESOUT=${{GESROOT}}/${{envir}}/nwgs/${{job}}.${{PDY}}
# nwges directory for input guess fields; typically $GESROOT/$envir
export GESIN=${{GESROOT}}/${{envir}}/nwgs


# loop over nems.configure per model, also must match run_name
# COMIN com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
# COMINmodel com directory for incoming data from model model
export COMINatm=${{COMROOT}}/${{envir}}/${{NET}}/atm
export COMINwave=${{COMROOT}}/${{envir}}/${{NET}}/ww3
export COMINadc=${{COMROOT}}/${{envir}}/${{NET}}/adcirc
export COMINmeshdata=${{COMROOT}}/${{envir}}/${{NET}}/atmesh
export COMINnwm=${{COMROOT}}/${{envir}}/${{NET}}/nwm

mkdir -p $INPUTdir $RUNdir $TMPdir $LOGdir $COMOUT $GESOUT
##############################################
# Execute the script
${{HOMEnsem}}/scripts/ex{}
##############################################

#startmsg
msg="JOB $job HAS COMPLETED NORMALLY."
# postmsg $jlogfile "$msg"

if [ -e $pgmout ]; then
    cat $pgmout
fi

cd $DATAROOT

if [ "$KEEPDATA" != YES ]; then
    rm -rf $DATA
fi

date

""".format(self.RUN+".sh")

        outfile = os.path.join(self.jjob_dir(), "J"+self.RUN.upper())
        # running two storms at once, even for testing, overrides ecf files
        # p = self.storm_dir("job")
        # outfile = os.path.join(p, "J"+self.RUN.upper())
        with open(outfile, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", outfile])

        print("\nProcessed ecflow jjob script %s" %outfile)


        # create the script at the same time as jjob
        out = os.path.join(self.script_dir(),"ex"+self.RUN+".sh")

        # this script must exists that does the real work
        p = os.path.join(self.ush_dir(), self.RUN+".py")
        if not found(p):
            print("Warrning - make sure to prepare the script!")

        dash = len("===========================")
        sblank = ""
        for i in range(dash - len(self.NET)):
            sblank += " "

        dash = len("=========================================")
        rblank = ""
        for i in range(dash - len(self.RUN)):
            rblank += " "

        lines="""
echo "============================================================="
echo "=                                                            "
echo "=         RUNNING NSEM FOR STORM: {}{}
echo "=         RUN NAME: {}{}
echo "=                                                            "
echo "============================================================="
#
python ${{USHnsem}}/{}

echo "{} completed"
exit 0
""".format(self.NET, sblank + '"', self.RUN, rblank + '"', self.RUN+".py", self.RUN)

        with open(out, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", out])

        print("\nProcessed ecflow script %s" %out)




class NEMSModel:

    def __init__(self, name, **kwargs):

        # holds kwargs i.e. attributes, petlist, ...
        self.__dict__.update({'Verbosity':'max'})  # default a must
        self.__name = name
        self.__dict__.update(**kwargs)


    @property
    def name(self):
        # i.e. ww3
        return self.__name


    @name.setter
    def name(self, name):
        self.__name = name


    def get_alias(self):
        name = self.name
        return self.__dict__[name.upper()+"_model"]


    def get_attributes(self):
        name = self.name
        return self.__dict__[name.upper()+"_attributes"]


    def get_petlist(self):
        """ gets pets lower and upper index """
        name = self.name
        return self.__dict__[name.upper()+"_petlist_bounds"]




class NEMSConfig():

    """ processes nems, nems.configure and model_configure file in PRJ_DIR/repo_name """

    def __init__(self, repo_name, node, user_module):

        self.source_dir = repo_name     
        self.node = node
        self.user_module = user_module


    def nems_config(self):
        return os.path.join(self.source_dir, 'nems.configure')


    def model_config(self):
        return os.path.join(self.source_dir, 'model_configure')


    def node(self):
        return self.node

    @property
    def user_module(self):
        return self.__user_module


    @user_module.setter
    def user_module(self, module):
        self.__user_module = os.path.join(self.source_dir,'modulefiles', self.node, module)
        return(self.__user_module)


    def earth_model_names(self):
        return self.__dict__['EARTH_component_list']


    def nems_models(self):
        # holds a list of NEMSModel objects
        return self.__dict__['NEMS_component_list']


    def setup_model_config(self, mc):
        '''creates a new model_config from initial values'''
        model_cf = self.model_config()
        print("\nWriting NEMS model config file %s" %model_cf)
                 
        try:
          lines="""# NEMS model_configure - autogenerated by NSEM at {}
print_esmf:              .true.
RUN_CONTINUE:            .false.
ENS_SPS:                 .false.
total_member:            {}
PE_MEMBER01:             {}

start_year:              {}
start_month:             {}
start_day:               {}
start_hour:              {}
start_minute:            {}
start_second:            {}
nhours_fcst:             {}
""".format(now(frmt=3), 
           mc['total_member:'], mc['PE_MEMBER01:'], mc['start_year:'],mc['start_month:'],
           mc['start_day:'], mc['start_hour:'],mc['start_minute:'],mc['start_second:'],
           mc['nhours_fcst:'])       
        except OSError as err:
          print("\nError on 'model_configure' values in initialization file - {0}\n".format(err))
          sys.exit(0)
 
        try:
          with open(model_cf, 'w+') as fptr:
            fptr.write(lines)
        except Exception as e:
          print("Error writing to %s\n" %(model_cf))
       

    def setup_nems_config(self, nc):
        '''creates a new nems.configure from initial values'''
        nems_cf = self.nems_config()
        print("Writing NEMS config file %s" %nems_cf)

        earth_comp = nc['EARTH_component_list:']
        earth_str = " ".join([i.strip() for i in earth_comp])

        atm_model = nc['ATM_model:']
        atm_str, atm_pet = atm_model
        atm_start, atm_end = atm_pet
        atm_pet_str = str(atm_start) + " " + str(atm_end)

        ocn_model = nc['OCN_model:']
        ocn_str, ocn_pet = ocn_model
        ocn_start, ocn_end = ocn_pet
        ocn_pet_str = str(ocn_start) + " " + str(ocn_end)

        wav_model = nc['WAV_model:'] 
        wav_str, wav_pet = wav_model
        wav_start, wav_end = wav_pet
        wav_pet_str = str(wav_start) + " " + str(wav_end)

        nwm_model = nc['NWM_model:']
        nwm_str, nwm_pet = nwm_model
        nwm_start, nwm_end = nwm_pet
        nwm_pet_str = str(nwm_start) + " " + str(nwm_end)

        run_seq = nc['runSeq::']['coupling_interval_sec']



        try:
          lines="""# nems.configure - autogenerated by NSEM at {}
#############################################
####  NEMS Run-Time Configuration File  #####
#############################################

# EARTH #
EARTH_component_list: {}
EARTH_attributes::
  Verbosity = max
::

# ATM #
ATM_model:                      {} 
ATM_petlist_bounds:             {} 
ATM_attributes::
  Verbosity = max
::

# OCN #
OCN_model:                      {}
OCN_petlist_bounds:             {} 
OCN_attributes::
  Verbosity = max
::

# WAV #
WAV_model:                      {}
WAV_petlist_bounds:             {}
WAV_attributes::
  Verbosity = max
::

# HYD #
NWM_model:                      {}
NWM_petlist_bounds:             {}
NWM_attributes::
  Verbosity = max
::

# Run Sequence #
runSeq::
  {}
    ATM -> OCN   :remapMethod=redist
    WAV -> OCN   :remapMethod=redist
    ATM -> NWM   :remapMethod=redist
    WAV -> NWM   :remapMethod=redist
    OCN -> NWM   :todo
    ATM
    WAV
    OCN
    NWM

  @
::

""".format(now(frmt=3), earth_str, atm_str, atm_pet_str, 
           ocn_str, ocn_pet_str, wav_str, wav_pet_str, 
           nwm_str, nwm_pet_str,
           run_seq
          )
        except OSError as err:
          print("\nError on 'model_configure' values in initialization file - {0}\n".format(err))
          sys.exit(0)

        try:
          with open(nems_cf, 'w+') as fptr:
            fptr.write(lines)
        except Exception as e:
          print("Error writing to %s\n" %(nems_cf))
        

    def read_model_config(self):

        model_cf = self.model_config()
        print("\nReading NEMS model config file %s" %model_cf)

        try:
          with open(model_cf,'r') as fptr:
            lines = fptr.readlines()
            for line in lines:
              if line.startswith("#") or len(line) < 2:
                continue
              key, value = line.split(":")
              if 'start_year' in key:
                self.start_year = value.strip()
              elif 'start_month' in key:
                self.start_month = value.strip()
              elif 'start_day' in key:
                self.start_day = value.strip()
              elif 'start_hour' in key:
                self.start_hour = value.strip()
              elif 'start_minute' in key:
                self.start_minute = value.strip()
              elif 'start_second' in key:
                self.start_second = value.strip()
              elif 'nhours_fcst' in key:
                self.nhours_fcst = value.strip()
        except Exception as e:
          print("\n%s" %str(e))
          sys.exit(-1)

        print("Runtime duration since: %s/%s/%s %s:%s:%s for %s hours\n" %(self.start_year,self.start_month,self.start_day,
               self.start_hour, self.start_minute, self.start_second, self.nhours_fcst))


    def get_duration(self):
        date_time_str = "%s/%s/%s %s:%s:%s" %(self.start_day, self.start_month, self.start_year,
                                              self.start_hour, "00", "00")
        self.start_date = datetime.datetime.strptime(date_time_str, '%d/%m/%Y %H:%M:%S')
        self.start_date_str = date_time_str
        return self.start_date, self.start_date_str


    def get_fcst_hours(self):
        return int(self.nhours_fcst)



    def read_nems_config(self):

        nems_cf = self.nems_config()
        print("\nReading NEMS config file %s" %nems_cf)

        try:
          with open(nems_cf,'r') as fptr:
            cnt = 0; sentinel = '::'
            # saves the line # of the "::" in file nems.configure
            indx = []
            lines = fptr.readlines()
            for line in lines:
              cnt += 1
              if line.startswith(sentinel):
                indx.append(cnt)

            # cut each section of the file based on indx
            earth_list = []; model_list = []; seq_list = []

            earth_list = lines[:indx[0]]
            model_list = lines[indx[0]:indx[len(indx)-2]]
            seq_list = lines[indx[len(indx)-2]:]

            # persists newely writen config files into __dic__ 
            self.process_earth_section(earth_list)
            self.process_model_section(model_list)
            self.process_runseq_section(seq_list)

        except Exception as e:
            print("\n%s" %str(e))
            sys.exit(-1)




    def get_num_tasks(self):
        """find the larget petlist number and save it as part of NEMSModel
           object for use in Slurm job """
        pl = []
        for model in self.nems_models():
            name = model.name
            petlist = model.get_petlist()
            pl.append(petlist[1])
        return max(pl)



    def print_model(self):
        for model in self.nems_models():
            name = model.name
            petlist = model.get_petlist()
            attrs = model.get_attributes()
            alias = model.get_alias()
            print("Model Name      : %s" %name)
            print("Model Alias     : %s" %alias)
            print("Model petlist   : %s" %petlist)
            print("Model attributes: %s" %attrs)
        print("\n")



    def process_earth_section(self, earth_lines):

        sentinel = '::'; i=0

        # lines are not cleaned yet
        lines = [line.strip() for line in earth_lines if len(line) > 1]
        line = lines[i]

        while line:
          #print("Line {}: {}".format(i, line.strip()))

          if re.search('EARTH_component_list', line, re.IGNORECASE) :
            k,v = line.split(":")     # Use v if decided to persists earth models as string instead of list

            models = list(v.split(" "))
            self.__dict__['EARTH_component_list'] = [model.strip() for model in models if len(model) > 1]
            i += 1
            line = lines[i]

          elif re.search('EARTH_attributes', line, re.IGNORECASE) :    # do not use :: becasue it might have space between!
            self.__dict__['EARTH_attributes'] = {}
            i += 1
            line = lines[i]

            while line.find(sentinel) == -1:
              dic = self.__dict__['EARTH_attributes']
              k,v = line.split("=")
              dic[k.strip()] = v.strip()
              self.__dict__['EARTH_attributes'] = dic
              i += 1
              line = lines[i]
            break

          else:
            i += 1
            line = lines[i]

        print("Pocessed EARTH_component_list")
        print(self.__dict__['EARTH_component_list'], "\n")


    def process_model_section(self, model_lines):

      sentinel = '::'; cnt = 0
      lines = [line.strip() for line in model_lines if len(line) > 2]
      line = lines[cnt]


      self.__dict__['NEMS_component_list'] = []
      tmp = []       # array for holding many NEMSModel objects
      i = 0          # counter of number of models in EARTH_component_list

      while( i < len(self.__dict__['EARTH_component_list']) ):
          model = self.__dict__['EARTH_component_list'][i]
          #print("Processing line %d, %s-%s, %d\n" %(cnt, line, model, i))

          if re.search(model+"_model", line, re.IGNORECASE) :   # do not use : becasue it might have space between!
              k,v = line.split(":")
              self.__dict__[model+"_model"] = v.strip()
              # print("1 - ", k, v.strip())
              cnt += 1
              line = lines[cnt]

          elif re.search(model+"_petlist_bounds", line, re.IGNORECASE) :
              k,v = line.split(":")
              v_int = [int(i) for i in list(v.strip().split(" "))]
              self.__dict__[model+"_petlist_bounds"] = v_int
              # print("2 - ", k, v_int)
              cnt += 1
              line = lines[cnt]

          elif re.search(model+"_attributes", line, re.IGNORECASE):
              self.__dict__[model+"_attributes"] = {}
              cnt += 1
              line = lines[cnt]
              while line.find(sentinel) == -1:
                  dic = self.__dict__[model+"_attributes"]
                  k,v = line.split("=")
                  dic[k.strip()] = v.strip()
                  self.__dict__[model+"_attributes"] = dic
                  cnt += 1
                  line = lines[cnt]
              # print("3 - ", k, dic)

              # update before breaking
              kwargs = { model+"_petlist_bounds":self.__dict__[model+"_petlist_bounds"],
                         model+"_attributes":self.__dict__[model+"_attributes"],
                         model+"_model":self.__dict__[model+"_model"]}
              tmp.append(NEMSModel(model,**kwargs))
              i += 1     # go to the next model in the list

          else:
              cnt += 1   # lines with comment or extera
              line = lines[cnt]



      # update before breaking
      self.__dict__['NEMS_component_list'] = tmp

      print("Processed models_component_list")
      self.print_model()



    def process_runseq_section(self, runseq_lines):

      sentinel = '::'; i = 0
      lines = [line.strip() for line in runseq_lines]
      line = lines[i]

      while True :
        # for now put this as common property -TODO
        if re.search('runSeq', line, re.IGNORECASE) :
          self.__dict__["runSeq"] = []
          vals = self.__dict__['runSeq']
          i += 1
          line = lines[i]

          while line.find(sentinel) == -1:
            vals.append(line.strip())
            i += 1
            line = lines[i]

          self.__dict__["runSeq"] = vals
          break
        else:
          i += 1
          line = lines[i]

      print("Processed runSeq")
      print(self.__dict__['runSeq'],"\n")


class NEMSBuild():

    """ This class creates a build script and copies the build file
        into PRJ_DIR/repo_name, the same level as NEMS source location.
        Then runs the script to compile the system.

        It doesn't check for he correctness of the directory structure.
        It assumes all model's source are in same level of NEMS.

        # unique prj_dir sturcture is expected to be in this format per NCO standards:
        <PRJ_DIR>/     maps to NCO variable ==> ${NWROOT}
           |--- nsem??                      ==> HOMEmodel (i.e. $NWROOT/model.v X.Y.Z)  TODO - do we need this level??
           |--- sorc/ADC_WW3_NWM_NEMS       ==> sorc
           |     |--- NEMS/   conf/   parm/   modulefiles/   model_configure  nems.configure  nems_env.sh  parm
           |     |--- NWM/  WW3/  ADCIRC/  ATMESH/
           |     |--- esmf-impi-env.sh   build.sh   nems.job
           |     |---
           |     |---
           |--- ecf/   jobs/   scripts/   exec/*   fix/*   parm/*   /ush*

         All stared "*" directories have defined variables in NCO in the form of "VARmodel" (i.e. USHnsem, PARMnsem).
         See files in jobs/ directory where these variables are set.
    """


    def __init__(self, nems_cfg):

        self.nems_cfg = nems_cfg
        self.source_dir = self.nems_cfg.source_dir

        # we need the build.sh script to be available
        self.write_build()


    def write_build(self):

        user_module = self.nems_cfg.user_module
        nems_models = self.nems_cfg.nems_models

        p = os.path.join(self.source_dir,'build.sh')

        junk, modulefile = user_module.split(self.source_dir)

        lines = """#!/bin/bash\n
# Description : Script to compile NSEModel NEMS application 
# Usage       : ./build.sh
# Date        : Autogenerated by NSEM at {}\n
# Contacts    : beheen.m.trimble@noaa.gov
#               saeed.moghimi@noaa.gov
#               andre.vanderwesthuysen@noaa.gov
#               ali.abdolali@noaa.gov

# load modules
source {}

cd NEMS\n""".format(now(2), modulefile[1:])    # remove the '/' from string

        lines += '\n#clean up\n'

        for model in nems_models():
            alias = model.get_alias().upper()
            if not exist(os.path.join(self.source_dir, alias)):
                print("\nDirectory %s not found!" %alias)

            lines += 'make -f GNUmakefile distclean_' + \
                      alias + ' COMPONENTS=' + \
                      '"' + alias + '"\n'

        lines += 'make -f GNUmakefile distclean_NEMS COMPONENTS="NEMS"\n'

        lines += '\n#make\n'
        lines += 'make -f GNUmakefile build COMPONENTS="'

        for model in nems_models():
            alias = model.get_alias().upper()
            lines +=  alias+ ' '
        lines = lines[:-1] + '"\n'

        with open(p, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", p])


        # save
        self.build_script = p
        print("Processed build script %s" %p)



    def build_nems_app(self):

        try:
            print("Start compiling ............\n")
            subprocess.check_call(['./build.sh'], cwd=self.source_dir, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            print('Error in executing build.sh: ', err)




class SlurmJob():

    # this class requires information from nems.configure,
    def __init__(self, **kwargs):

        self.__dict__.update(**kwargs)

        if 'error' in kwargs:
            self.error = "j" + kwargs['error'] + ".err.log"
        if 'output' in kwargs:
            self.output = "j" + kwargs['output'] + ".out.log"
        if 'jobname' in kwargs:
            self.jobname = "j" + kwargs['jobname'] + ".job"


    def get_sbatch(self):
        return self.sbatch_part


    def print_kw(self):
        print(self.__dict__)


    def write_sbatch(self):

        slurm_file = os.path.join(self.__dict__['slurm_dir'], self.jobname[1:])   # no j in this name, using this in standalone runs not in WCOSS

        sbatch_part = """#!/bin/sh -l\n
#SBATCH -A {}
#SBATCH -q {}
#SBATCH -e {}
#SBATCH --output={}
#SBATCH --ignore-pbs
#SBATCH -J {}
#SBATCH --mail-user={}
#SBATCH --ntasks-per-node={}
#SBATCH -N {}
#SBATCH --parsable
#SBATCH -t {}""".format(self.__dict__['account'], self.__dict__['queue'], self.error, self.output,self.jobname,
                        self.__dict__['mailuser'], self.__dict__['ntasks'], self.__dict__['nnodes'], self.__dict__['time'])

        # for use by other classes
        self.sbatch_part = sbatch_part

        lines = """\n\n############################### main - to run: $sbatch {} ##########################
set -x
echo $SLURM_SUBMIT_DIR		# (in Slurm, jobs start in "current dir")
echo $SLURM_JOBID
echo $SLURM_JOB_NAME
echo $SLURM_NNODES
echo $SLURM_TASKS_PER_NODE\n
echo $SLURM_NODELIST		# give you the list of assigned nodes.\n
echo 'STARTING THE JOB AT'
date\n
# change to absolute path of where you pulled the
# NEMS and NEMS Applications. use modules.nems becasue user's
# modulefiles are copied into this with constant name.
cp -fv {}/NEMS/exe/NEMS.x NEMS.x
source {}/NEMS/src/conf/modules.nems
srun ./NEMS.x
date
""".format(self.jobname, PRJ_DIR, PRJ_DIR )

        with open(slurm_file, 'w') as f:
            f.write(sbatch_part+lines)
        print("\nProcessed slurm job file %s" %slurm_file)



class NEMSRun():

    # this class requires information from NCOSystem and SlurmJob
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)  # TODO - add check that all args are in kwargs



class BlankLinesHelpFormatter (argparse.HelpFormatter):
    # add empty line if help lines ends with \n
    # default with=54
    def _split_lines(self, text, width):

        # default _split_lines removes final \n and reduces all interior whitespace to one blank
        lines = super()._split_lines(text, width)
        if text.endswith('\n'):
            lines += ['']
        return lines


def prep_nwm(dic):
    """
    check follwing files for configuration parameters and then copy
    into $COMIN/nwm: setEnvar.sh, namelist.hrldas, hydro.namelist
    pre-process the inputfiles located at ??? and ln into $COMIN/nwm
    """
    nwm_data_path = "/scratch2/COASTAL/coastal/save/COASTAL_ACT_NWC/NWM-v2.1/Data/assimilation"
    domain = os.path.join(nwm_data_path,"domain","CONUS")
    forcing = os.path.join(nwm_data_path,"forcing",dic['storm'])
    slices = os.path.join(nwm_data_path,"nudgingTimeSliceObs",dic['storm'])
    restart = os.path.join(nwm_data_path,"restart",dic['storm'])

    p = dic['COMINnwm']
    print("Preparing NWM input data in %s" %p )

    if not exist(p):
      try:
        subprocess.run(['mkdir', '-pv', p ], check=True)
      except subprocess.CalledProcessError as err:
        print('Error preparing NWM: ', err)

    dirs = [domain, forcing, slices, restart]
    alias = ['DOMAIN', 'FORCING', 'nudgingTimeSliceObs', 'RESTART']
    for dir, name in zip(dirs,alias):
      if os.path.islink(os.path.join(p,name)) and os.path.exists(os.path.join(p,name)):
        continue
      else:
        try:
          subprocess.run(['ln', '-s', dir, name ], check=True, cwd=p)
        except subprocess.CalledProcessError as err:
          print('Error linking %s: ' %err)

    files = ['namelist.hrldas', 'hydro.namelist', 'CHANPARM.TBL', 'GENPARM.TBL', 'HYDRO.TBL', 'MPTABLE.TBL', 'SOILPARM.TBL']
    for f in files:
      file = os.path.join(nwm_data_path, f)
      try:
        subprocess.run(['cp', file, '.' ], check=True, cwd=p)
      except subprocess.CalledProcessError as err:
        print('Error copying files %s: ' %err)



def import_initfile(filename):

    directory, module_name = os.path.split(filename)
    module_name = os.path.splitext(module_name)[0]

    path = list(sys.path)
    sys.path.insert(0, directory)
         
    try:
        module = __import__(module_name) 
        return module
    finally:
        sys.path[:] = path # restore



def import_ini(args=None):

    # get the input from the nsem_ini.py file
    try:
      print("Importing initialization file, nsem_ini.py .....")
      ini = import_initfile(args.ini)       # TO DO - check for correct format of init file
    except Exception as err:
      print("\nError importing initialization file {} - {0}\n".format(args.ini,err))
      sys.exit(0)

    return ini
 


def nsem_workflow(args=None):

    ini = import_ini(args)
    try:
      node = ini.node
      envir = ini.envir
      event = ini.STORM
      run_name = ini.RUN_TYPE
      global PRJ_DIR
      PRJ_DIR = ini.PRJ_DIR   # location where nco system directory is to be constructed, if not exists
      global RUN_DIR
      RUN_DIR = ini.RUN_DIR   # "/scratch2/COASTAL/coastal/scrub/com/nsem"  # Note: nsem part of com dir!!
    except OSError as err:
      print("\nError reading initialization file {} - {0}\n".format("nsem_ini.py",err))
      sys.exit(0)

    # these 3 to be verified for their final place 
    DATAROOT = os.path.join("/tmp",event.lower())
    GESROOT = RUN_DIR
    model = ini.model

    if not exist(PRJ_DIR):
      print("Project directory %s doesn't exist, please check and rerun the program\n" %PRJ_DIR)
      sys.exit(0)

    
    # construct model input/output paths, if none exists
    # or creates the none existing ones
    print("\nConstructing NCO system directory structure .....")
    nco = NCOSystem(event, envir, run_name, DATAROOT, GESROOT, model)
    nco.setup_rundir()
    nco.setup_prjdir()
    return nco, ini



def git_nsem(repo, nco_sorc_dir):
    
    print("\nCloning {} to {}".format(repo, nco_sorc_dir)) 

    # dest_dir is the name part of the repo and so it becomes
    # the location of NEMS and all the models. This is one layer
    # below ROOTDIR, as mentioned in NEMS HOWTO.
    dest_dir = os.path.join(nco_sorc_dir, Path(repo).name)
    if exist(dest_dir):
       print("\nRemoving directory: {}".format(dest_dir))
       try:
           subprocess.run(['rm', '-rf', dest_dir ], check=True)
       except subprocess.CalledProcessError as err:
           print('Error deleting directory: ', err)

    cmd = ['git', 'clone', '--recursive', repo]      # TO DO - add the user/pass
    try:   
      # must wait to finishe, so check_call or run
      return subprocess.check_call(cmd, cwd=sorc_dir, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
      print("Exception on process, rc=", e.returncode)
    
        
def setup_libs():    
    # setup other libs and add to nems user module, if possible - TO DO
    """
    ParMETIS:
    module purge  
    module load intel impi  
    setenv CFLAGS -fPIC  
    make config cc=mpiicc cxx=mpiicc prefix=/path/to/your/parmetis/ | & tee config.out-rr  
    make install | & tee make-install.out-rr  
    This adds libparmetis.a under /path/to/your/parmetis/lib/libparmetis.a
    Set the path to ParMETIS:
    setenv METIS_PATH /path/to/your/parmetis  
    """



def build_nsem(args=None):

    nco, ini = nsem_workflow(args)        # all models and nems and nems configs should be located in this dir

    sorc_dir = nco.source_dir()

    # git nsem models + nems from repo 
    # conda install  gitpython
    repo = ini.repository
    if ini.git_flag:
        git_nsem(repo, sorc_dir)            # TODO - check on the repo version, status, etc

    # setup_libs()

    node = ini.node
    nems = ini.nems
    user_module = nems['user_module']
    mc = ini.model_configure
    nc = ini.nems_configure

    # populate NEMS model class and process nems configure files
    # needed for creation of build script
    dest_repo = os.path.join(sorc_dir, Path(repo).name)    # where we clone nsem models + nems in sorc_dir
    # this method updates nco_sorc to dest_repo from here on. 
    # nems_cf has access to this.
    nems_cf = NEMSConfig(dest_repo, node, user_module)
    nems_cf.setup_model_config(mc)
    nems_cf.setup_nems_config(nc)
    """ to test the write """
    nems_cf.read_nems_config()
    nems_cf.read_model_config() 
    

    # compile the codes and submit the job to run
    nems_build = NEMSBuild(nems_cf)   # TODO pickle
    if ini.compile_flag:
        nems_build.build_nems_app()


    # SlurmJob needs update by reading nems.configure,
    # update slurm_args
    ntasks = nems_cf.get_num_tasks()
    walltime = nems_cf.get_fcst_hours()           # are they the same ??
    start_date, start_date_str = nems_cf.get_duration()
    # note: slurm_source_dir = dest_repo = nems_cf.source_dir, nems_build.source_dir 
    # print(ntasks, walltime, start_date, start_date_str, dest_repo)

    slurm_args = ini.slurm_args
    # update the "TBD" values in nsem_ini.py file
    slurm_args['ntasks'] = ntasks
    slurm_args['slurm_dir'] = dest_repo
    slurm = SlurmJob(**slurm_args)
    slurm.write_sbatch()
    
    # ecflow file constructions, requires info from both Slurm and NCO
    nco.write_ecf2(slurm)
    nco.write_jjob2()

    # create a importable file of all the environments needed
    nco.write_helper(nems_cf)

    sys.exit(0)
    dic = {'storm': event, 'COMINnwm': nco.COMINnwm}
    prep_nwm(dic)
    # cp NEMS.x /scratch2/COASTAL/coastal/scrub/com/nsem/para/florence
    # cp model_configure nems.configure /scratch2/COASTAL/coastal/scrub/com/nsem/para/florence

    # nems_run = NEMSRun(**run_args)

    print("\n")



if __name__ == '__main__':

    usage = Color.F_Red + "\n"
    usage += "%s --help | -h \n"  %sys.argv[0]
    usage += Color.F_Default
    print(usage)

    parser = argparse.ArgumentParser()
    subp = parser.add_subparsers()
   
    nco = subp.add_parser("workflow", help="reads an initialization file and construct the NSEM workflow")
    nco.add_argument("--ini", help="an init python file with prepopulated values", default="nsem_ini.py")
    nco.set_defaults(func=nsem_workflow)
    

    build_install = subp.add_parser("build", help="buils and installs NSEM models with NEMS")
    build_install.add_argument("--ini", help="an init python file with prepopulated values", default="nsem_ini.py")
    build_install.set_defaults(func=build_nsem)
  

    args = parser.parse_args()
    print(args)
    args.func(args)

