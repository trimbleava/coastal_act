# NSEM initialization file, import this into all the sources.

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

slurm_args = {
	'account':'coastal','ntasks':782,'nnodes':'34','queue':'test',
	'time':8,'jobname':'todo', 'error':'run_name',
	'output':'run_name','mailuser':'??', 'slurm_dir': 'source_dir'
}

nems_configure = {
	'EARTH_component_list:': ['OCN'],     # ['ATM','OCN','WAV','NWM'],
        'ATM_model:': ['atmesh', (11,11)],    # name, petlist_bounds
        'OCN_model:': ['adcirc', (0,10)],
        'WAV_model:': ['ww3',    (12,12)],
        'NWM_model:': ['nwm',    (13,781)],
	'runSeq::'  : {'coupling_interval_sec': '@3600',}
}


