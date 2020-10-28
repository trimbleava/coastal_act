"""
Description : NSEM initialization file - this initialization puts all the configuration variables required by below configuration files into one!
              NEMS nems.config, NEMS model_configure, NSEM model configurations, Slurm batch config, NCO configuration
Run         : conda activate /scratch2/COASTAL/coastal/save/NAMED_STORMS/PYTHON_ENVS/nems_venv3.7
Date        : 7/6/2020
Developer   : Coastal Act
"""

import os


valid_runs = {                         					# nsem
        "tide_baserun":        "Tide-only forecast run with ADCIRC",
        "best_track2ocn":      "Best-track ATMdata used to force live ADCIRC",
        "wav&best_track2ocn":  "Best-track ATMdata and WAVdata used to force live ADCIRC",
        "atm2ocn":             "ATMdata used to force live ADCIRC",
        "wav2ocn":             "WAVdata used to force live ADCIRC",
        "atm&wav2ocn":         "ATMdata and WAVdata used to force live ADCIRC",
        "atm2wav2ocn":         "ATMdata used to force live ADCIRC and WW3",
        "forecast":            "atm_adc_ww3_nwm",
        "tide_spinup":         "is this same as the first one??"
}

STORM = "matthew"         		                                # nsem - a.k.a event 
RUN_TYPE = "forecast"							# nsem - a.k.a run_name, run_type

repository = "https://github.com/moghimis/ADC-WW3-NWM-NEMS"             # nsem models + NEMS
compile_flag = 0                                                        # 1 to compile the nsem code, 0 not to compile
git_flag = 0                                                            # 1 to git NSEM code from repo, 0 not to git

NWM = {
        'nwm_data_path': "/scratch2/COASTAL/coastal/save/COASTAL_ACT_NWC/NWM-v2.1/Data/assimilation",
        'domain'       : 'Gulf',   # this needs to be set per storm location, choices (Base, Gulf, Atlantic, CONUS)
        'domain_files' : ['Fulldom_hires_netcdf_file_250m_FullRouting_NWMv2.1.nc', 'GEOGRID_LDASOUT_Spatial_Metadata_1km_NWMv2.1.nc',
                          'GWBUCKPARM_FullRouting_NWMv2.1.nc', 'LAKEPARM_NWMv2.1.nc', 'GWBUCKPARM_LongRange_NWMv2.1.nc',
                          'RouteLink_NWMv2.1.nc', 'geo_em.d01.conus_1km_NWMv2.1.nc', 'hydro2dtbl_FullRouting_NWMv2.1.nc',
                          'nudgingParam_NWMv2.1.nc', 'soil_properties_FullRouting_NWMv2.1.nc', 'spatialweights_250m_FullRouting_NWMv2.1.nc',
                          'wrfinput.d01.conus_1km_NWMv2.1.nc' ],
        'restart_files': [os.path.join(STORM,'HYDRO_RST.yyyy-mm-dd_00_00_DOMAIN1'),  
                          os.path.join(STORM,'RESTART.yyyymmddhh_DOMAIN1'),  
                          os.path.join(STORM, 'nudgingLastObs.yyyy-mm-dd_00_00_00.nc') ],
        'forcing_files': [os.path.join(STORM,'yyyymmddhh.LDASIN_DOMAIN1')],
        'nudging_timeslice_obs_files': [os.path.join(STORM, 'yyyy-mm-dd_hh:mm:ss.15min.usgsTimeSlice.ncdf')],
        'config_files' : ['namelist.hrldas', 'hydro.namelist'],
        'table_files'  : ['CHANPARM.TBL', 'GENPARM.TBL', 'HYDRO.TBL', 'MPTABLE.TBL', 'SOILPARM.TBL'],
      }
##

slurm_args = {								# slurm
        'account':'coastal','ntasks':'TBD','nnodes':'TBD','queue':'test',
        'time':8,'jobname':RUN_TYPE, 'error':RUN_TYPE,
        'output':RUN_TYPE,'mailuser':'coastal.act@noaa.gov', 'slurm_dir': 'TBD'
}

##

nems = { 'user_module': "ESMF_NUOPC"}  					# nems - NEMS module file 

nems_configure = {                                                      # nems - NEMS nems_configure
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

model_configure = { 		                                        # nems - NEMS model.configure
        # make sure this matches EARTH_component_list, above
        'total_member:':     4,
        'PE_MEMBER01:' :     0,
        'start_year:'  : '2016',
        'start_month:' :   '10',
        'start_day:'   :   '01',
        'start_hour:'  :   '00',
        'start_minute:':    '0',
        'start_second:':    '0',
        'nhours_fcst:' :    23 * 24         # 23 days * 24 hours
}

total_member = 4							# nems - NEMS model.configure
PE_MEMBER01 = 0
start_year = '2008'
start_month = '09'
start_day = '04'
start_hour = '06'
start_minute = '0'
start_second = '0'
nhours_fcst =  72

## watch for use of variables - do not use dic here
node = "hera"                           # nco
envir = "para"                          # nco
model = "nsem"                          # nco
# compile_flag = 0                        # nco
PRJ_DIR = "/scratch2/COASTAL/coastal/save/COASTAL_ACT_NWC/Apps/CA_TEST"            # coastal_act"     # nco 
RUN_DIR = "/scratch2/COASTAL/coastal/scrub/com/nsem"                            # nco

# Enviroment vars from ecFlow scripting                                         # nco
NWROOT = PRJ_DIR
FIXnsem = os.path.join(NWROOT,"fix")
EXECnsem = os.path.join(NWROOT,"exec")
SORCnsem = os.path.join(NWROOT,"sorc") 
PARMnsem = os.path.join(NWROOT,"parm")
USHnsem = os.path.join(NWROOT,"ush")
GESIN = os.path.join(NWROOT,"nwgs")
#
COMIN = os.path.join(RUN_DIR,envir,STORM)
COMINatm = os.path.join(COMIN,"atm")
COMINwave = os.path.join(COMIN,"ww3")
COMINwavedata = os.path.join(COMIN,"ww3data")
COMINmeshdata = os.path.join(COMIN,"atmesh")
COMINadc = os.path.join(COMIN,"adcirc")
COMINnwm = os.path.join(COMIN,"nwm")
jlogfile = os.path.join(RUN_DIR,envir,"logs","jlogfile."+RUN_TYPE) #/scratch2/COASTAL/coastal/scrub/com/nsem/para/logs/jlogfile.nwm_test
