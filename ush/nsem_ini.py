"""
Description : NSEM initialization file - this initialization puts all the configuration variables required by below configuration files into one!
              NEMS nems.config, NEMS model_configure, NSEM model configurations, Slurm batch config, NCO configuration
Run         : conda activate /scratch2/COASTAL/coastal/save/NAMED_STORMS/PYTHON_ENVS/nems_venv3.7
Date        : 7/6/2020
Developer   : Beheen M. Trimble - Coastal Act
"""

node = "hera"                           # nco
envir = "para"                          # nco
storm = "shinnecock"      		# nsem - a.k.a event - nsem
nems_user_module = "ESMF_NUOPC"         # nems - NEMS module file 
model_run = "nwm_test"   		# nsem - a.k.a run_name, run_type - for real runs select from valid_runs below
prj_dir = "/scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT"     # nco 
run_dir = "/scratch2/COASTAL/coastal/scrub/com/nsem"                    # nco

# flags
compile_flag = 0                                                        # nco


# see if these are needed to be inited! TODO                            # nsem
valid_runs = {
	'tide_baserun':        'Tide-only forecast run with ADCIRC',
	'best_track2ocn':      'Best-track ATMdata used to force live ADCIRC',
	'wav&best_track2ocn':  'Best-track ATMdata and WAVdata used to force live ADCIRC',  
	'atm2ocn':             'ATMdata used to force live ADCIRC',  
	'wav2ocn':             'WAVdata used to force live ADCIRC',  
	'atm&wav2ocn':         'ATMdata and WAVdata used to force live ADCIRC',  
	'atm2wav2ocn':         'ATMdata used to force live ADCIRC and WW3', 
	'forecast':            'atm_adc_ww3_nwm',
        'tide_spinup':         ' is this same as the first one??'
}

slurm_args = {                                                          # slurm
	'account':'coastal','ntasks':'TBD','nnodes':'34','queue':'test',
	'time':8,'jobname':model_run, 'error':model_run,
	'output':model_run,'mailuser':'beheen.m.trimble@gmail.com', 'slurm_dir': 'TBD'
}

nems_configure = {                                                      # nems
	'EARTH_component_list:': ['OCN'],     # ['ATM','OCN','WAV','NWM'],
        'ATM_model:': ['atmesh', (11,11)],    # name, petlist_bounds
        'OCN_model:': ['adcirc', (0,10)],
        'WAV_model:': ['ww3',    (12,12)],
        'NWM_model:': ['nwm',    (13,781)],
	'runSeq::'  : {'coupling_interval_sec': '@3600',}
}

model_configure = {
        'total_member:':     2,
        'PE_MEMBER01:' :     0,
        'start_year:'  : '2008',
        'start_month:' :   '09',
        'start_day:'   :   '04',
        'start_hour:'  :   '06',
        'start_minute:':    '0',
        'start_second:':    '0',
        'nhours_fcst:' :    72
}
