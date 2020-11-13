"""
File Name   : nsem_ini.py
Description : NSEM initialization file - this initialization puts all the configuration variables required by below configuration files into one!
              NEMS nems.config, NEMS model_configure, NSEM model configurations, Slurm batch config, NCO configuration
Usage       : conda activate /scratch2/COASTAL/coastal/save/NAMED_STORMS/PYTHON_ENVS/nems_venv3.7
Date        : 7/6/2020
Contacts    : Coastal Act Team 
              ali.abdolali@noaa.gov, saeed.moghimi@noaa.gov, beheen.m.trimble@gmail.com, andre.vanderwesthuysen@noaa.gov
"""

import os
from datetime import datetime

STORM = "matthew"         		                                # nsem - a.k.a event 
RUN_TYPE = "atm2wav2ocn2hyd"					        # nsem - a.k.a run_name, run_type
PRJ_DIR = "/scratch2/COASTAL/coastal/save/COASTAL_ACT_NWC/Apps/CA_TEST" # coastal_act"  
COM_DIR = "/scratch2/COASTAL/coastal/scrub/com/nsem"                    # nsem
RUN_DIR = "/scratch2/COASTAL/coastal/scrub/nsem_run"                    # nsem, I think this is the working directory per nco!!


repository = "https://github.com/moghimis/ADC-WW3-NWM-NEMS"             # nsem models + NEMS
compile_flag = 0                                                        # 1 to compile the nsem code, 0 not to compile
git_flag = 0                                                            # 1 to git NSEM code from repo, 0 not to git


slurm_args = {								# slurm
        'account':'coastal','ntasks':32,'nnodes':26,'queue':'debug',
        'time':8,'jobname':RUN_TYPE, 'error':RUN_TYPE,
        'output':RUN_TYPE,'mailuser':'coastal.act@noaa.gov', 'slurm_dir': 'TBD'
}

##

nems = { 'user_module': "ESMF_NUOPC"}  					# nems - NEMS module file 

# hydro stream team has pre-defined nems.configure per runtype in 
# nco parm directory. To be consistent and to be scalable, file name 
# to this file is set here. This means user is also responsible
# to prepare and located this file in nco parm directory per runtype. 
# The older version of this keyword is kept both at the end of this file
# as well as the code in workflows for the historical reason.
# Note: the existence of this file is checked during the build process.
nems_configure = {'nems_cfg': 'nems.configure.'+RUN_TYPE}

model_configure = { 		                                        # nems - NEMS model.configure
        # make sure this matches EARTH_component_list, above
        # The RUN_CONTINUE flag tells us if the RUN step of the
        # NEMS component must be called multiple times for ensembles. 
        'print_esmf'  : '.true.',
        'run_continue': '.false.',
        'ens_sps'     : '.false.',        
        'total_member':     4,
        'pe_member01' :     0,
        'start_year'  : '2016',
        'start_month' :   '10',
        'start_day'   :   '01',
        'start_hour'  :   '00',
        'start_minute':    '0',
        'start_second':    '0',
        'nhours_fcst' : 10 * 24   # 10 days * 24 hours
}


## watch for use of variables - do not use dic here
node = "hera"                           # nco
envir = "para"                          # nco
model = "nsem"                          # nco


########################## Almost statics

valid_runs = {                                                          # nsem
        "tidebaserun":          "Tide-only forecast run with ADCIRC",
        "besttrack2ocn":        "Best-track ATMdata used to force live ADCIRC",
        "wavbesttrack2ocn":     "Best-track ATMdata and WAVdata used to force live ADCIRC",
        "atm2ocn":              "ATMdata used to force live ADCIRC",
        "wav2ocn":              "WAVdata used to force live ADCIRC",
        "atmwav2ocn":           "ATMdata and WAVdata used to force live ADCIRC",
        "atm2wav2ocn":          "ATMdata used to force live ADCIRC and WW3",
        "atm2hyd":              "ATMdata used to force live NWM",
        "atm2ocn2hyd":          "ATMdata used to force live ADCIRC and NWM",
        "tidespinup":           "is this same as the first one??",
        "atm2wav2ocn2hyd":      "ATMdata used to force live Wave and ADCIRC and NWM - final"
}


NWM = {
        'nwm_data_path': "/scratch2/COASTAL/coastal/save/COASTAL_ACT_NWC/NWM-v2.1/data/assimilation",
        'domain'       : 'CONUS',   # preprocess per storm location, choices (Base, Gulf, Atlantic, CONUS)
        #
        'domain_files' : {'fulldom': 'Fulldom_hires_netcdf_file_250m_FullRouting_NWMv2.1.nc',
                          'geogrid': 'GEOGRID_LDASOUT_Spatial_Metadata_1km_NWMv2.1.nc',
                          'gbucketparm': 'GWBUCKPARM_FullRouting_NWMv2.1.nc', 'lakeparm': 'LAKEPARM_NWMv2.1.nc',
                          'routelink': 'RouteLink_NWMv2.1.nc', 'geom': 'geo_em.d01.conus_1km_NWMv2.1.nc',
                          'hydrotbl': 'hydro2dtbl_FullRouting_NWMv2.1.nc',
                          'nudgingparm': 'nudgingParam_NWMv2.1.nc', 'soilprop': 'soil_properties_FullRouting_NWMv2.1.nc',
                          'spweight': 'spatialweights_250m_FullRouting_NWMv2.1.nc',
                          'wrfinput': 'wrfinput.d01.conus_1km_NWMv2.1.nc' },
        #
        'restart_files': {'hydro': 'HYDRO_RST.yyyy-mm-dd_00_00_DOMAIN1',
                          'restart': 'RESTART.yyyymmddhh_DOMAIN1',
                          'nudginglastobs': 'nudgingLastObs.yyyy-mm-dd_00_00_00.nc'
                         },
        #
        'forcing_files': ['yyyymmddhh.LDASIN_DOMAIN1'],
        # for compilation needs *.sh to be preprocessed and located in parm dir.
        # (i.e. ./compile_nuopc_NoahMP.sh setEnvar.sh esmf-impi-env.sh)
        # Note: esmf-impi-env.sh is for all models and should be coordinated with
        # NEMS user_module
        # during compilation, configs and tables are overwritten, therefore these
        # files need to be preprocessed and copied into nwm data dir either during prep
        # process or before running the models. 
        #
        # I preprocessed all these files and saved a copy in CPL/NUOPC/Template dir
        # that is being archived in repo for persistency. I use this copy from the
        # Template directory to copy them into parm and standalone data location of
        # of the nwm (i.e. NWM-v2.1/data/assimilation)
        # needs.
        'env_files'    : {'env': 'setEnvar.sh', 'esmf': 'esmf-impi-env.sh' },                            # preprocess in nco parm dir
        #
        'config_files' : {'namelist': 'namelist.hrldas', 'hydro': 'hydro.namelist'},                     # preprocess in nwm data dir
        #
        'table_files'  : ['CHANPARM.TBL', 'GENPARM.TBL', 'HYDRO.TBL', 'MPTABLE.TBL', 'SOILPARM.TBL'],    # preprocess in nwm data dir
        #
        'nudgingTimeSliceObs_files': ['yyyy-mm-dd_hh:mm:00.15min.usgsTimeSlice.ncdf']
        #
      }
                                                                   

# Enviroment vars from ecFlow scripting                                         # nco
NWROOT = PRJ_DIR
FIXnsem = os.path.join(NWROOT,"fix")
EXECnsem = os.path.join(NWROOT,"exec")
SORCnsem = os.path.join(NWROOT,"sorc") 
PARMnsem = os.path.join(NWROOT,"parm")
USHnsem = os.path.join(NWROOT,"ush")
GESIN = os.path.join(NWROOT,"nwgs")
#
COMIN = os.path.join(COM_DIR,envir,STORM)
COMINatm = os.path.join(COMIN,"atm")
COMINwave = os.path.join(COMIN,"ww3")
COMINwavedata = os.path.join(COMIN,"ww3data")
COMINmeshdata = os.path.join(COMIN,"atmesh")
COMINadc = os.path.join(COMIN,"adcirc")
COMINnwm = os.path.join(COMIN,"nwm")
#
# DATAROOT Directory containing the working directory, often /tmpnwprd1 in production
# is DATAROOT same as what we see as run_dir?
# Note: becasue we are not sure about this RUNdir and because it is named by date
#       we are including this as the workflow yet. We create this at the prep step for now.
now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d")
RUNdir = os.path.join(RUN_DIR,STORM+"."+RUN_TYPE +"."+ date_time)
#
jlogfile = os.path.join(RUN_DIR,envir,"logs","jlogfile."+RUN_TYPE) #/scratch2/COASTAL/coastal/scrub/com/nsem/para/logs/jlogfile.nwm_test

# in nco parm directory now. Code still is in workflows but
# decided to use prepared configs like other hydro streams. 
nems_configure_old = {                                                      # nems - NEMS nems_configure
        # eliminate model from this list only, do not touch the rest
        # TODO do we need this to be align with build.sh? order and number of models
        'EARTH_component_list:': ['ATM','OCN','WAV','NWM'],
                   # model name, petlist_bounds
        # do not touch these - let's discuss
        'ATM_model:': ['atmesh', (11,11)],
        'OCN_model:': ['adcirc', (0,10)],
        'WAV_model:': ['ww3data',    (12,12)],                          # either ww3data or ww3
        'NWM_model:': ['nwm',    (13,781)],
        'runSeq::'  : {'coupling_interval_sec': '@3600',}
}

