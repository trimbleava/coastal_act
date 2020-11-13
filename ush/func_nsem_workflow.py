#!/usr/bin/env python

"""
File Name   : func_nsem_workflow.py
Description : NSEM directory structure builder based on NCO standards
Usage       : Import this into an external python program such as main.py (i.e. import func_nsem_workflow as fnw)
              then run the main program: python main.py workflow --ini=nsem_ini.py
Date        : 7/6/2020
Contacts    : Coastal Act Team 
              ali.abdolali@noaa.gov, saeed.moghimi@noaa.gov, beheen.m.trimble@gmail.com, andre.vanderwesthuysen@noaa.gov
"""

# standard libs
import glob, os, sys
import datetime, subprocess

# local libs
import nsem_utils as nus


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

    # unique run_dir is constructed by this format - Note: currenty COM_DIR includes the nsem

    """ $COMROOT/$NET/$envir/$RUN.$PDY
        COMIN com directory for current model's input data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        COMOUT com directory for current model's output data, typically $COMROOT/$NET/$envir/$RUN.$PDY
        COMINmodel com directory for incoming data from model model

    <COM_DIR>/                                              ==> ${COMROOT}/
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
    'COMROOT' : COM_DIR,     # let's call this com_dir
    'GESROOT' : GESROOT,     # let's have this in comroot/nwges
    'DATAROOT': DATAROOT,    # let's mak this on /tmp<storm>|/tmp<nsem>
    'NWROOT'  : PRJ_DIR      # let's call this prj_dir

    """

    def __init__(self, event, envir, run_name, dataroot, gesroot, model="nsem"):

        self.COMROOT = COM_DIR               # COMROOT root directory for input/output data on current system
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
export COM_DIR={}
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
                "COMdir = os.getenv('COMdir')",
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

        # this print comes after export helper, do not change the \n here
        print("Processed helper environment script %s\n" %outfile)  


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
        if not nus.exist(p):
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
        if not nus.exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
                subprocess.check_call(['mkdir', '-v', self.SOURCE, self.SCRIPT, self.ECF, self.FIX,
                                       self.USH, self.EXEC, self.PARM, self.JOBS], cwd=p)
            except subprocess.CalledProcessError as err:
                print('Error in creating model home directory: ', err)
        else:
            for dir in self.prj_dir():
                if not nus.exist(dir):
                    try:
                      subprocess.run(['mkdir', '-vp', dir ], check=True)
                    except subprocess.CalledProcessError as err:
                      print('Error in creating %s directory: ' %(dir, err))
                #else:
                #    print("\n%s is healthy" %dir)

        # now check on subdirs:
        for dir in self.prj_subdir():
            if not nus.exist(dir):
                try:
                  subprocess.run(['mkdir', '-vp', dir ], check=True)
                except subprocess.CalledProcessError as err:
                  print('Error in creating %s directory: ' %(dir, err))
            #else:
            #    print("\n%s is healthy" %dir)

    # rundir is not clear yet! - TODO
    def setup_rundir(self):
        pass


    # Com dir and subdir
    def com_subdir(self):
        subdir_iterable = ['nwm', 'adcirc', 'ww3', 'atmesh', 'atm']
        for subdir in subdir_iterable:
            yield subdir


    def setup_comdir(self):
        p = self.COMIN
        print("Checking health of com directory: {}".format(p))
        if not nus.exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating model input directory: ', err)

        for dir in self.com_subdir():
            subdir = os.path.join(p, dir)
            if not nus.exist(subdir):
                try:
                  subprocess.run(['mkdir', '-vp', subdir ], check=True)
                except subprocess.CalledProcessError as err:
                  print('Error in creating %s directory: ' %(subdir, err))


        """created on script side with id
        p = self.COMOUT
        if not nus.exist(p):
            print("\nCreating model output directory: {}".format(p))
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating model input directory: ', err)
        """

        p = self.GESIN
        print("Checking restart directory: {}".format(p))
        if not nus.exist(p):
            try:
                subprocess.run(['mkdir', '-pv', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating gesin directory: ', err)


        """created on script side with id
        p = self.GESOUT
        if not nus.exist(p):
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
        if not nus.exist(p):
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
                self.RUN, nus.now(2))

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
                self.RUN, nus.now(2))

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
export COMdir=${{COMdir:-${{DATA}}/run}}
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
mkdir -p $INPUTdir $COMdir $TMPdir $LOGdir $COMOUT $GESOUT
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

""".format(nus.now(4), self.NET, self.job, self.NWROOT, self.fix_dir(), self.exec_dir(),
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
        if not nus.found(p):
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

        print("Processed ecflow script %s" %out)



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
export COMdir=${{COMdir:-${{DATA}}/run}}
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

mkdir -p $INPUTdir $COMdir $TMPdir $LOGdir $COMOUT $GESOUT
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

        print("Processed ecflow jjob script %s" %outfile)


        # create the script at the same time as jjob
        out = os.path.join(self.script_dir(),"ex"+self.RUN+".sh")

        # this script must exists that does the real work
        p = os.path.join(self.ush_dir(), self.RUN+".py")
        if not nus.found(p):
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

        print("Processed ecflow script %s" %out)



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
      ini = nus.import_file(args.ini)       # TO DO - check for correct format of init file
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
      global COM_DIR
      COM_DIR = ini.COM_DIR   # "/scratch2/COASTAL/coastal/scrub/com/nsem"  # Note: nsem part of com dir!!
    except OSError as err:
      print("\nError reading initialization file {} - {0}\n".format("nsem_ini.py",err))
      sys.exit(0)

    # these 3 to be verified for their final place 
    DATAROOT = os.path.join("/tmp",event.lower())
    GESROOT = COM_DIR
    model = ini.model

    # construct model input/output paths, if none exists
    # or creates the none existing ones
    print("\nChecking NCO system directory structure .....")
    nco = NCOSystem(event, envir, run_name, DATAROOT, GESROOT, model)
    nco.setup_prjdir()
    nco.setup_comdir()
    # nco.setup_rundir()     # TODO - not clear at this time
    return nco, ini

