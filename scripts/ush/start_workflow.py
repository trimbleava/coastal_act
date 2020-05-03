#!/usr/bin/env python


# standard libs
import glob, os, sys, re, time, argparse
import datetime, subprocess


# local libs
from color import Color, Formatting, Base, ANSI_Compatible


# globals - updated during reading command line
PRJ_DIR = os. getcwd() 
RUN_DIR = os.getcwd()


def now(frmt=1):

    now = datetime.datetime.now()

    if frmt == 1:
        now = now.strftime("%Y-%m-%d %H:%M:%S")
    elif frmt == 2:
        now = now.strftime("%b. %d, %Y")
    elif frmt == 3:
        now = now.ctime()

    return now


def exist(path):
    p = os.path.abspath(path)
    if os.path.isdir(p):
        return 1
    return 0


def found(file):

    f = os.path.abspath(file)
    if not os.path.isfile(f):
        msg = Color.F_Red + "\nFile {} not found!\n".format(file) 
        msg += Color.F_Default
        print(msg)
    return 1


class NCOSystem:

    SOURCE = 'sorc'
    SCRIPT = 'scripts'


    def source_dir(self):
        return os.path.join(PRJ_DIR, self.SOURCE) 


    def script_dir(self):
        return os.path.join(PRJ_DIR, self.SCRIPT) 




class NEMSConfig(NCOSystem):

    """ processes nems.configure file in PRJ_DIR 
        TODO - no need to read entire conf so far, only get 
        the model list and copy configs to run_dir 
    """

    def __init__(self, node, user_module):

        super(NCOSystem, self).__init__()

        self.node = node
        self.user_module = user_module

        self.read_nems_config()
        self.read_model_config()    #TODO


    def nems_config(self):
        return os.path.join(self.source_dir(), 'nems.configure')


    def model_config(self):
        return os.path.join(self.source_dir(), 'model_configure')


    def node(self):
        return self.node

    @property
    def user_module(self):
        return self.__user_module


    @user_module.setter
    def user_module(self, module):
        self.__user_module = os.path.join(self.source_dir(),'modulefiles', self.node, module)
        return(self.__user_module)


    def earth_model_names(self):
        return self.__dict__['EARTH_component_list']


    def nems_models(self):
        return self.__dict__['NEMS_component_list']


    def read_model_config(self):
        pass


    def read_nems_config(self):

      nems_cf = self.nems_config()
      if not found(nems_cf):
          sys.exit(0)

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

        self.process_earth_section(earth_list)
        self.process_model_section(model_list)
        self.process_runseq_section(seq_list)
        # print(self.__dict__)



    def process_earth_section(self, earth_lines):

        sentinel = '::'; i=0

        # lines are not cleaned yet
        lines = [line.strip() for line in earth_lines if len(line) > 1]
        line = lines[i]

        while line:
          #print("Line {}: {}".format(i, line.strip()))

          if re.search('EARTH_component_list', line, re.IGNORECASE) :
            k,v = line.split(":")
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

        print("\nFinished processing EARTH_component_list.")



    def process_model_section(self, model_lines):
      sentinel = '::'; cnt = 0
      lines = [line.strip() for line in model_lines if len(line) > 2] 
      line = lines[cnt]

      self.__dict__['NEMS_component_list'] = []      # introduced a new list, could be extra and overkill!!
      tmp = []

      for model in self.__dict__['EARTH_component_list']:

          while True :
              #print("line is %s" %(line))
              if re.search(model+"_model", line, re.IGNORECASE) :   # do not use : becasue it might have space between!
                  k,v = line.split(":")

                  self.__dict__[model+"_model"] = v.strip()

                  tmp.append(NEMSModel(v.strip()))

                  cnt += 1
                  line = lines[cnt]

              elif re.search(model+"_petlist_bounds", line, re.IGNORECASE) :
                  k,v = line.split(":")
                  v_int = [int(i) for i in list(v.strip().split(" "))]
                  self.__dict__[model+"_petlist_bounds"] = v_int
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

                  # update before breaking
                  self.__dict__['NEMS_component_list'] = tmp
                  break

              else:
                  cnt += 1
                  line = lines[cnt]

      print("\nFinished processing models_component_list.")


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

      print("\nFinished processing runSeq.")


class NEMSBuild(NEMSConfig):

    """ This class creates a build script and copies the build file
        into PRJ_DIR, the same level as NEMS source location.
        Then runs the script to compile the system.

        It doesn't check for for the correctness of NEMS dir.
        It assumes all model's source are in same level of NEMS.
        
    """
    def __init__(self):

        super(NEMSBuild, self).__init__ (node, user_module)   # must be same name as its parent

        self.write()
        self.build_nems_app()



    def write(self):


        if not found (self.user_module):
            sys.exit(0)

        junk, modulefile = self.user_module.split(self.source_dir())

        lines = """#!/bin/bash\n
# Description : Script to compile NSEModel NEMS application
# Date        : {}\n
# Developer   : beheen.m.trimble@noaa.gov
# Contributors: saeed.moghimi@noaa.gov
#               andre.vanderwesthuysen@noaa.gov
#               ali.abdolali@noaa.gov
# load modules
source {}\n   
cd NEMS\n""".format(now(2), modulefile[1:])    # remove the '/'

        lines += '\n#clean up\n'


        for model in self.nems_models():
            if not found (os.path.join(self.source_dir(), model.name)):
                sys.exit(0)


            lines += 'make -f GNUmakefile distclean_' + \
                      model.name + ' COMPONENTS=' + \
                      '"' + model.name + '"\n'

        lines += 'make -f GNUmakefile distclean_NEMS COMPONENTS="NEMS"\n'

        lines += '\n#make\n'
        lines += 'make -f GNUmakefile build COMPONENTS="'

        for model in self.nems_models():
            lines += model.name + ' '
        lines = lines[:-1] + '"\n'

        p = os.path.join(self.source_dir(),'build.sh')
        with open(p, 'w') as fptr:
            fptr.write(lines)

        # change mode
        subprocess.call(["chmod", "a+x", p])


        # save 
        self.build_script = p 

        print("\nFinished writing {}".format(p))



    def build_nems_app(self):

        try:
            print("\nStart compiling ............\n")

            subprocess.run(['./build.sh'], cwd=self.source_dir(), check=True)
        except subprocess.CalledProcessError as err:
            print('Error in executing build.sh: ', err)

        print("\nFinished compiling ............\n")



class NEMSModel:

    def __init__(self, name, **kwargs):

        self.__dict__.update({'Verbosity':'max'})  # default a must
        self.__name = name.upper()
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



class NEMSInstall(NEMSConfig):

    # unique run_dir is constructed by this format
    """
    <RUN_DIR>/
        |--- <model_name>/
        	|--- <event>/
                	|--- <input_data>
        		|
        		|--- <scenario>/
               			|--- <out_data>/

    """
    def __init__(self, domain, event, run_name):

        super(NEMSInstall, self).__init__(node, user_module)   # must be same name as its parent

        self.input = event 
        self.output = (event, run_name)


    @property
    def output(self):
        return self.__output

    @output.setter
    def output(self, val):
        name = "NSEM_DATA"
        event, run_name = val
        self.__output = os.path.join(RUN_DIR, name, event, run_name)


    @property
    def input(self):
        return self.__input


    @input.setter
    def input(self, event):
        tmp = []
        for model in self.nems_models():
            name = model.name
            name += "_DATA"
            tmp.append(os.path.join(RUN_DIR, name, event))
        self.__input = tmp


    def install_dir(self):
        for p in nems_install.input:
            if not exist(p):
                print("\nCreating model input directory: {}".format(p))
                try:
                    subprocess.run(['mkdir', '-p', p ], check=True)
                except subprocess.CalledProcessError as err:
                    print('Error in creating model input directory: ', err)
     
        p = nems_install.output
        if not exist(p):
            print("\nCreating model output directory: {}\n".format(p))
            try:
                subprocess.run(['mkdir', '-p', p ], check=True)
            except subprocess.CalledProcessError as err:
                print('Error in creating model output directory: ', err)

        
class NEMSRun:
    pass

                      

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


class BlankLinesHelpFormatter (argparse.HelpFormatter):
    # add empty line if help lines ends with \n
    # default with=54
    def _split_lines(self, text, width):

        # default _split_lines removes final \n and reduces all interior whitespace to one blank
        lines = super()._split_lines(text, width)
        if text.endswith('\n'):
            lines += ['']
        return lines



if __name__ == '__main__':

    print("\n")  # this is to print nicer
    prog = sys.argv[0]
    usage = Color.F_Blue + "%s\n"  %prog
    usage += Color.F_Red
    usage += "       %s --help | -h \n"  %prog
    usage += "       %s -d <domain> -n <node> -e <event> -u <user_module> -s <run_name> -b <prj_dir> -i <run_dir>\n" %(prog)
    usage += "       %s --domain <domain> --node <node> --event <event> --module <user_module> --scenario <run_name> --build <prj_dir> --install <run_dir>\n" %(prog)
    usage += "       %s -d <domain> -e <event> -s <run_name> -i <run_dir>\n" %(prog)
    usage += Color.F_Default 

    desc = '''This script builds one or more coupled models with NEMS and/or installs the system into a pre-defined location, ready to run.\n'''
    parser = argparse.ArgumentParser(prog=prog, usage=usage, add_help=True,
                                     formatter_class=BlankLinesHelpFormatter,
                                     description=desc, epilog='\n')

    parser.add_argument('-b', '--build', dest='prj_dir', type=str, default=PRJ_DIR,  
                        help='''Compiles, links, and creates libraries from the models source files using the NEMS coupler. Location of the coupled system could be provided by the user, as long as the specified location complies with the expected structure. The default build directory is {}\n'''.format(PRJ_DIR)) 
                                 
    parser.add_argument('-i', '--install', dest='run_dir', type=str, default=RUN_DIR, 
                        help='''Installs a previously NEMS built system into a NEMS compliance user defined directory. The default install directory is {}\n'''.format(RUN_DIR))

    parser.add_argument('-d', '--domain', dest='domain_name', type=str, default="CONUS", help='CONUS or Gulf or Atlantic\n')
    parser.add_argument('-n', '--node', dest='node_name', type=str, help='Name of the machine your are running this program from such as "hera". This name must be the same name as in conf/configure.nems.hera.<compiler>\n')
    parser.add_argument('-e', '--event', dest='event_name', type=str, help='A Named Storm Event Model such as "Sandy"\n')
    parser.add_argument('-u', '--module', dest='user_module', type=str, help='NEMS user module name, located in modulefiles\n')
    parser.add_argument('-s', '--scenario', dest='run_name', type=str, help='A unique name for this model run\n')
    parser.add_argument('-m', '--models', dest='model_list', type=str, help='Comma separated model directory names where the model source code resides at the same level of NEMS source codes. No space before and after commas. The model names are case sensative. Example: ADCIRC,WW3,NWM\n')

    args = parser.parse_args()
    print(len(sys.argv))

    if len(sys.argv) == 11 :
        # ./start_workflow.py -d conus -n hera -e sandy -u ESMF_NUOPC -s baserun
        if exist(args.prj_dir) and exist(args.run_dir):
            print("\nbuilding in {} and installing into {}\n".format(PRJ_DIR, RUN_DIR))
            PRJ_DIR = os.path.abspath(args.prj_dir); RUN_DIR = os.path.abspath(args.run_dir)
        else:
            print("\nAbsolute path {} or {} not found!\n".format(args.prj_dir,args.run_dir))
            sys.exit(0) 


    elif len(sys.argv) == 15:
        # ./start_workflow.py -d conus -n hera -e sandy -u ESMF_NUOPC -s baserun -b /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT -i /scratch2/COASTAL/coastal/save/NAMED_STORMS/NEMS_APP/NEMS_RUN
        if exist(args.prj_dir) and exist(args.run_dir):
            print("\nbuilding in {} and installing into {}\n".format(args.prj_dir, args.run_dir))
            PRJ_DIR = os.path.abspath(args.prj_dir); RUN_DIR = os.path.abspath(args.run_dir)
        else:
            print("\nAbsolute path {} or {} not found!\n".format(args.prj_dir,args.run_dir))
            sys.exit(0) 
    else:
        print("\nWrong number of command line arguments\n")
        print(usage)
        sys.exit(0)

    # ./start_workflow.py -d conus -n hera -e sandy -u ESMF_NUOPC -s baserun -b /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT -i /scratch2/COASTAL/coastal/save/NAMED_STORMS/NEMS_APP/NEMS_RUN


    # options in slurm job
    j = {'account':'coastal', 'queue':'debug', 'error':'slurm.error', 'jobname':'nsem',
         'mailuser':'beheen.m.trimble@noaa.gov', 'ntasks':24, 'nodes':32, 'time':420,
         'batch':'nsem.job', 'rootdir':os.getcwd()}

    node = 'hera'                                       # computer node
    models = ['ADCIRC', 'WW3DATA', 'ATMESH', 'NWM']     # coupled list of models
    event = 'ike'                                       # storm event
    user_module = 'ESMF_NUOPC'                          # NEMS user modulefiles 
    scenarios = ['TBD']                                 # model runs with specific objective in mind
    nems_cf = 'nems.configure'



    # local variables
    domain = node = event = user_module_name = run_name = ""

    domain = args.domain_name
    node = args.node_name
    event = args.event_name
    user_module_name = args.user_module
    run_name = args.run_name

    # populate the system path
    #nco = NCOSystem()  this is populated on call to NEMSConfig

    # populate nems and process nems configure files
    nems_cfg = NEMSConfig(node, user_module_name)

    # compiles the codes
    nems_build = NEMSBuild()   # TODO pickle


    # unique run_dir is constructed by this format
    """
    <RUN_DIR>/
	|--- <model_name>/
		|--- <event>/
			|--- <input_data>
			|
			|--- <scenario>/
				|--- out1
		                |--- out2                                           

    """
    # construct model input/output paths
    nems_install = NEMSInstall(domain, event, run_name)

    # creates input/output  directory structure if they don't exist
    nems_install.install_dir()

