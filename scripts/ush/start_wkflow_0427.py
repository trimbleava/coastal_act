import os, sys, re
import datetime


def now(frmt=1):

    now = datetime.datetime.now()

    if frmt == 1:
        now = now.strftime("%Y-%m-%d %H:%M:%S")
    elif frmt == 2:
        now = now.strftime("%b. %d, %Y")
    elif frmt == 3:
        now = now.ctime()

    return now


class NEMSConfigure:
    """ creates nems.configure file in RUN_DIR """

    # TODO add allowed list
    def __init__(self, **kwargs):
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)

    def read(self, nems_cf):

      with open(nems_cf,'r') as fptr:
        found = 0; sentinel = '::'
        line = fptr.readline()
        while line:
          #print("Line {}: {}".format(cnt, line.strip()))
          if re.search('EARTH_component_list', line, re.IGNORECASE) :
            k,v = line.split(":")
            models = list(v.split(" "))
            self.__dict__['EARTH_component_list'] = [model.strip() for model in models if len(model) > 1]

          elif re.search('EARTH_attributes', line, re.IGNORECASE) :    # do not use :: becasue it might have space between!
            self.__dict__['EARTH_attributes'] = {}
            found = 1
            line = fptr.readline()
            while line.find(sentinel) == -1:
              dic = self.__dict__['EARTH_attributes']
              k,v = line.split("=") 
              dic[k.strip()] = v.strip()
              self.__dict__['EARTH_attributes'] = dic
              line = fptr.readline()

          elif 'EARTH_attributes' in self.__dict__:
            
            for model in self.__dict__['EARTH_component_list']:
              while line.startswith(model) != 0 :
                line = fptr.readline()
            
                if re.search(model+"_model", line, re.IGNORECASE) :   # do not use : becasue it might have space between!
                  k,v = line.split(":")
                  self.__dict__[model+"_model"] = v.strip()

                elif re.search(model+"_petlist_bounds", line, re.IGNORECASE) :
                  k,v = line.split(":") 
                  v_int = [int(i) for i in list(v.strip().split(" "))]
                  self.__dict__[model+"_petlist_bounds"] = v_int

                elif re.search(model+"_attributes", line, re.IGNORECASE):
                  self.__dict__[model+"_attributes"] = {}
                  line = fptr.readline()
                  while line.find(sentinel) == -1:
                    dic = self.__dict__[model+"_attributes"]
                    k,v = line.split("=")
                    dic[k.strip()] = v.strip()
                    self.__dict__[model+"_attributes"] = dic
                    line = fptr.readline()
     

          line = fptr.readline()

        print(self.__dict__)


    def write(self):
        lines = """#############################################
####  NEMS Run-Time Configuration File  #####
#############################################\n
# EARTH #
EARTH_component_list: {} 
EARTH_attributes::
  Verbosity = max
::\n
"""
        head_lines = """# {} #
{}_model:                       {}
{}_petlist_bounds:              {} {}
{}_attributes::""".format(self.name.upper(),self.name.upper(),self.name.upper())

        attr_lines = '' 
        for attr, val in self.__dict__.items():
            attr_line += attr.capitalize()
            attr_lines += ' = '
            attr_lines += val         # string??
        attr_lines += '::'    

        seq_lines = '# Run Sequence #'
        seq_lines += 'runSeq::'
        seq_lines += """  @3600 
ATM -> OCN   :remapMethod=redist
WAV -> OCN   :remapMethod=redist
ATM
WAV
OCN
@
::
"""
        lines += head_lines.join(attr_lines).join(seq_lines)
        with open('nems.configure','w') as fptr:
            fptr.write(lines)



class NEMSModel:
    
    def __init__(self, name, **kwargs):
  
        self.__dict__.update({'Verbosity':'max'})  # default a must
        self.__name = name
        self.__dict__.update(**kwargs)
        
        
    @property
    def name(self):
        return self.__name


    @name.setter
    def name(self, name):
        self.__name = name


    def petlist(self,mode=1):
        """ sets and get pets lower and upper index """
        if mode == 1 :
            self.petbounds = self.__dict__.get('petlist_bounds')
        else:
            return self.__dict__.get('petlist_bounds', [-1,-1])


class ModelConf:
    pass


class ModelInstall:
    pass


class NEMSRun:
    pass


class NEMSBuild:
    """ this build script must be same level as NEMS location"""
    def __init__(self, models, node, module):
       self.models = models
       self.node = node
       self.module = module


    def write(self):
        lines = """#!/bin/bash\n
# Description : Script to compile NSEModel NEMS application
# Date        : {}\n
# load modules
source modulefiles/{}/{}\n   
cd NEMS\n""".format(now(2), self.node.lower(), self.module)

        lines += '\n#clean up\n'
        for model in self.models:
            lines += 'make -f GNUmakefile distclean_' + \
                      model.upper() + ' COMPONENTS=' + \
                      '"' + model.upper() + '"\n'
    
        lines += '\n#make\n'
        lines += 'make -f GNUmakefile build COMPONENTS="'
        for model in self.models:
            lines += model.upper() + ' '
        lines = lines[:-1] + '"\n'

        with open('build.sh', 'w') as fptr:
            fptr.write(lines)



class SlurmJob:

    def __init__(self, **kwargs):

        self.__dict__.update({'account':'coastal', 'queue':'test', 'error':'slurm.error', 'jobname':'nsem',
                              'mailuser':'beheen.m.trimble@noaa.gov', 'ntasks':24, 'nodes':32, 'time':420,
                              'batch':'nsem.job', 'rootdir':os.getcwd()})
      
        self.__dict__.update(**kwargs)


    def print_kw(self):
        print(self.__dict__)


    def write(self):

        lines = """#!/bin/sh -l\n
#SBATCH -A {}            # -A, --account=name - charge job to specified account
#SBATCH -q {}               # submit to this Q
#SBATCH -e {}        # -e, --error=err - file for batch script's standard error
#SBATCH --ignore-pbs          # --ignore-pbs - ignore #PBS options in the batch script
#SBATCH -J {}               # -J, --job-name=jobname - name of job (type = block|cyclic|arbitrary)
#SBATCH --mail-user={} # --mail-user=user - who to send email notification for job state changes
#SBATCH --ntasks-per-node={}  # --ntasks-per-node=nt - number of tasks to invoke on each node
#SBATCH -N {}                 # -N, --nodes=N - number of nodes on which to run (N = min[-max])
#SBATCH --parsable            # --parsable - outputs only the jobid and cluster name (if present),
                              # separated by semicolon, only on successful submission.
#SBATCH -t {}                # -t, --time=minutes - time limit\n
############################### main - to run: $sbatch {} ##########################
set -x
echo $SLURM_SUBMIT_DIR            # (in Slurm, jobs start in "current dir")   
echo $SLURM_JOBID                                                     
echo $SLURM_JOB_NAME
echo $SLURM_NNODES                                             
echo $SLURM_TASKS_PER_NODE\n
echo $SLURM_NODELIST              # give you the list of assigned nodes.\n
echo 'STARTING THE JOB AT'
date\n
# change the ROOTDIR to absolute path of where you pulled the 
# NEMS and NEMS Applications. use modules.nems becasue user's
# modulefiles are copied into this
cp -fv {}/NEMS/exe/NEMS.x NEMS.x
source {}/NEMS/src/conf/modules.nems
srun ./NEMS.x
date
""".format(self.account,self.queue,self.error,self.jobname,self.mailuser, self.ntasks,
                     self.nodes, self.time, self.batch, self.rootdir, self.rootdir)

        with open(self.batch, 'w') as f:
            f.write(lines)
 

if __name__ == '__main__':

    # options in slurm job
    j = {'account':'coastal', 'queue':'debug', 'error':'slurm.error', 'jobname':'nsem',
         'mailuser':'beheen.m.trimble@noaa.gov', 'ntasks':24, 'nodes':32, 'time':420,
         'batch':'nsem.job', 'rootdir':os.getcwd()}
    
    node = 'hera'                        # computer node
    models = ['ADCIRC','WW3', 'NWM']     # coupled list of models
    events = ['ike']                     # storm event
    module = ['ESMF_NUOPC']  # user modulefiles per NEMS - should we read it from the PRJ_DIR?
    scenarios = ['TBD']                  # model runs with specific objective in mind
    nems_cf = 'nems.configure'
 
    job = SlurmJob(**{'batch': 'nems.job'})
    job.write()
    
    build = NEMSBuild(models, node, module)
    build.write()

    nems_cf_obj = NEMSConfigure()
    nems_cf_obj.read(nems_cf)


