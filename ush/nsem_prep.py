#!/usr/bin/env python

# stdandard libs
import os, sys, time, subprocess, logging, shutil
import json
from datetime import datetime, timedelta
from dateutil.parser import parser
from string import Template

# third party libs
import numpy as np

# user defined libs
import nsem_env as env
import nsem_utils as util
import nsem_ini as ini

##########################################

"""
prepares model configurations, model input files, nems configuration per
storm and per run_name ready to be submitted to run.


questions:
what is the major work of nsem_prep? just input? input and spinup runs?
what is nws ??   dep. run_type
what are the PE runs used for and their relation to CA forecast run?
does tide and wave spin up always run before adc run?
tide_spinup','tide_baserun','best_track2ocn - not run_type??
How to calculate the spinup times? how to deal with < day remainder, set the 12.5, 27??
how get the wave and atm files during forecast time?
avail_options = [
    'tide_spinup',
    'atm2ocn',
     'wav2ocn',
    'atm&wav2ocn',
    ]
are these runs produces output that should be used in forcast run?
which option is required to be run back to back with forecast
how to calculate the spinup timing if the forcast hours is only few hours?
when False in base info runs?
how to read the nems.configure.xxx.IN files?
is storms directory ??
"""

logger = logging.getLogger(env.jlogfile)


def read_ini():
    """ reading user defined variables from initialization file, nsem_ini """
    ini_dict = {}
    try:
      with open('nsem_ini.py') as fptr:
        data = json.load(fptr)
    except Exception as err: 
        print("%s\n" %(str(err)))
        sys.exit(-1)

    
def get_tidal_fact(run_dir):
    """
    based on spin-up start time prepare tide fac to be used in fort.15.tempelate
    In:
    Out: tidal fact dictionary
    
    """
    txt1 = '   > Prepare Tidal factors ..'
    logf(txt1,log_file)

    duration = str ((base_info.wave_spin_end_date-base_info.tide_spin_start_date).total_seconds() /86400.)


    # copy tidal input file
    os.system('cp -f ' + PARMnsem + '/storms/' + STORM + '/tide_inp.txt ' + run_dir)

    tidefac_inp_file = os.path.join(run_dir, 'tide_inp.txt')
    tidefac_inp      = open(tidefac_inp_file,'w')
    # write data
    tidefac_inp.write( duration + ' \n')  #for 1 year
    tidefac_inp.write(str(base_info.tide_spin_start_date.hour) +' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.day)  +' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.month)+' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.year) +' ')
    tidefac_inp.close()

    #comm0 = "source " + modfile +' ; '
    comm1  = ' cd   ' + run_dir + ' ; '+tidefac +' <  tide_inp.txt  >  tidefac.log'
    #print(comm1)

    
    txt1 = comm1
    logf(txt1,log_file)      
    
    os.system(comm1)
    
    tidefac_dic = {}
    tidefac_out_file = os.path.join(run_dir, 'tide_fac.out')
    tidefac_out      = open(tidefac_out_file,'r')
    
    for line in tidefac_out.readlines():
        params = line.split()
        print(line)
        if 'K1'  in  params:    fft1,facet1   = params[1],params[2]
        if 'O1'  in  params:    fft2,facet2   = params[1],params[2]
        if 'P1'  in  params:    fft3,facet3   = params[1],params[2]
        if 'Q1'  in  params:    fft4,facet4   = params[1],params[2]
        if 'N2'  in  params:    fft5,facet5   = params[1],params[2]
        if 'M2'  in  params:    fft6,facet6   = params[1],params[2]
        if 'S2'  in  params:    fft7,facet7   = params[1],params[2]
        if 'K2'  in  params:    fft8,facet8   = params[1],params[2]
        if 'MF'  in  params:    fft9,facet9   = params[1],params[2]
        if 'MM'  in  params:    fft10,facet10 = params[1],params[2]
        if 'M4'  in  params:    fft11,facet11 = params[1],params[2]
        if 'MS4' in  params:    fft12,facet12 = params[1],params[2]
        if 'MN4' in  params:    fft13,facet13 = params[1],params[2]
    tidefac_out.close()
   
    return dict ( fft1=fft1,facet1=facet1,   
                  fft2=fft2,facet2=facet2,   
                  fft3=fft3,facet3=facet3,   
                  fft4=fft4,facet4=facet4,   
                  fft5=fft5,facet5=facet5,   
                  fft6=fft6,facet6=facet6,   
                  fft7=fft7,facet7=facet7,   
                  fft8=fft8,facet8=facet8,   
                  fft9=fft9,facet9=facet9,   
                  fft10=fft10,facet10=facet10, 
                  fft11=fft11,facet11=facet11, 
                  fft12=fft12,facet12=facet12, 
                  fft13=fft13,facet13=facet13
               ) 


def one_run_eq():
    run_dir = RUNdir
    #os.system('echo "cd  ' + run_dir +' " >> ' + run_scr )
    #os.system('echo "qsub qsub.sh      " >> ' + run_scr )
    #os.system('echo "sbatch slurm.sh    " >> ' + run_scr )
    #
    prep_nems(run_dir)
    prep_adc(run_dir)
    if base_info.run_option == 'atm2wav2ocn':
       prep_ww3(run_dir)

    if False:
        plot_domain_decomp(run_dir)
        back_up_codes(run_dir)



def spinup_time(ts=12.5,ws=27):

    """calculates spinup timing for both tide and wave 
       relative to forecast start time and end time """

    msg = "\nCalculating spinup time ....."
    print(util.colory("red",msg))

    duration = env.frcst_hrs
    start_date_str = env.start_date_str

    # string date to date object
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y %H:%M:%S')
    hours_added = timedelta(hours=duration)
    end_date = start_date + hours_added
    delta = end_date - start_date
    num_days = delta.days
    # print(start_date, end_date, num_days)

    # tide spinup start time must be 12 days prior to forecast start date
    tide_spin_start_date = start_date - timedelta(days=ts)
    # wave spinup star time must be 27 prior to start date
    wave_spin_start_date = start_date - timedelta(days=ws)

    tide_spin_end_date = tide_spin_start_date + timedelta(days=ts)
    wave_spin_end_date = wave_spin_start_date + timedelta(days=ws)
    # 2008-08-23 00:00:00
    # 2008-09-04 12:00:00
    # 2008-09-19 00:00:00
    # print("Start wave: %s\nStart tide: %s\nEnd tide  : %s\nEnd wave  : %s\nStart date: %s\nEnd date  : %s\n"                                          
    #        %(wave_spin_start_date, tide_spin_start_date, tide_spin_end_date,           
    #         wave_spin_end_date, start_date, end_date))

    msg = tide_spin_start_date, tide_spin_end_date, wave_spin_start_date, wave_spin_end_date, start_date, end_date
    logger.info(msg)
    return msg



def adc_atm_data(storm, provider):

    # copping atm data from COMINatm
    # (i.e. /scratch2/COASTAL/coastal/scrub/com/nsem/para/shinnecock/atm)

    atm_inp_dir     = env.COMINatm           # 'hsofs_forcings/ike_v2_7settings/inp_atmesh'
    wav_inp_dir     = env.COMINwav           # 'hsofs_forcings/ike_v2_7settings/inp_wavdata'

    # wave and atm files are 
    atm_netcdf_file_names = [
        '01_IKE_HWRF_OC.nc',
        '02_IKE_HWRF_OC_SM.nc',
        '03_IKE_WRF.nc',
        '04_IKE_HWRF_OC_WRF.nc',
        '05_IKE_HWRF_OC_DA_HSOFS_orig.nc',
        '06_IKE_HWRF_OC_DA_HSOFS_Smoothing.nc',
        '07_IKE_HWRF_OC_DA_WRF_SM.nc',
        ]



def adc_wave_data(storm, provider):
    msg = "\nCopping wave ata ....."
    print(util.colory("red",msg))
    return

    wav_netcdf_file_names = np.array([
        '01_ww3.test1.2008_sxy_OC.nc',
        '02_ww3.test2.2008_sxy_OC_SM.nc',
        '03_ww3.test3.2008_sxy_WRF.nc',
        '04_ww3.test4.2008_sxy_OC_WRF.nc',
        '05_ww3.test5.2008_sxy_OC_DA_HSOFS_orig.nc',
        '06_ww3.test6.2008_sxy_OC_DA_HSOFS_Smoothing.nc',
        '07_ww3.test7.2008_sxy_OC_DA_WRF_SM.nc',
        ])



def change_nws():
    """
    Go through all fort.15 files and change nws. I need
    this routine because adcprep still not addapted to handl nws=17.
  
    
    """
    import glob

    sys.exit( 'Fixed internally. Go ahead and chenge your main fort.15 if needed!')

    pattern = 'NWS'
    nws     = str (base_info.nws)
    line2replace  = ' ' +nws+ \
        '                                       ! NWS - WIND STRESS AND BAROMETRIC PRESSURE \n'
    #replace main fort.15
    filename = os.path.join(run_dir,'fort.15')
    replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )

    #replace fort.15 in PE directories

    dirs = glob.glob(run_dir + '/PE0*')

    for dir1 in dirs:
         filename = os.path.join(dir1,'fort.15')
         replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )

    print(' > Finished updating  fort.15s')
   #####
    pattern = 'NWS'
    nws     = str (base_info.nws)
    line2replace  = '       ' + nws + \
        '                        ! NWS, wind data type \n'
    filename = os.path.join(run_dir,'fort.80')
    replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )
    print(' > Finished updating  fort.80')



def update_fort15(dic):
    """update adcirc model parameter and periodic boundary condition 
       file (fort.15). fort.15 is a template file and it is updated
       once per storm and under certain condition per run-type"""

    # get information needed from nems_env.py file
    start_date_str = env.start_date_str
    duration = env.frcst_hrs

    # change the date format to what adcirc expects
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y %H:%M:%S')
    adcirc_start_date = start_date.isoformat().replace('T',' ')+ ' UTC'
    
    # saves the updateable parameters
    d15 = {}
    d15.update({'start_date'    :adcirc_start_date })
    d15.update({'run_time_days' :str(dic['ndays'])})

    d15.update({'dramp'         :str(dic['ndays_ramp'])})
    d15.update({'nws'           :str(dic['nws'])})
    d15.update({'ihot'          :str(dic['ihot'])})
    d15.update({'dt'            :str(dic['dt'])})
    d15.update({'hot_ndt_out'   :str(dic['hot_ndt_out'])})

    if dic['nws'] > 0:
        d15.update({'WTIMINC'       :str(base_info.WTIMINC)  })
        d15.update({'RSTIMINC'      :str(base_info.RSTIMINC)  })
        #os.system('cp -f ' + adc_inp + '/fort* ' + run_dir)
        #os.system('cp -f ' + adc_inp + '/*.sh  ' + run_dir)
        #os.system('cp -f ' + adc_inp + '/*.py  ' + run_dir)
        os.system ('cp -f ' + adc_inp + '/*.*   ' + run_dir)

    # get tide facts - TODO needs a condition
    
    #d15_tide = get_tidal_fact(run_dir)
    #d15.update(d15_tide)

    # get updated fort.15
    fort15tmp = os.path.join(env.FIXnsem,'meshes',env.storm,'ocn', dic['fort15_temp'])
    dest  = os.path.join(env.COMINadc,'fort.15')
    util.tmp2scr(filename=dest, tmpname=fort15tmp, d=d15)


def prep_nems(dic):
  
    """Prepare nems run files"""

    # build.sh

    # slurm.job

    # NEMS.x


    # nems model_configure   
    ocn_pet_num = 0; atm_pet_num = 0; wav_pet_num = 0; nwm_pet_num = 0

    # prepare nems.configure
    dc2={}
    dc2.update({'c'  :'#' })
    try:
      if 'ocn_name' in dic:
        dc2.update({'_ocn_model_': dic['ocn_name']})

      if 'ocn_petlist' in dic:
        dc2.update({'_ocn_petlist_bounds_': dic['ocn_petlist']})
        pet_nums_arr = dic['ocn_petlist'].split()
        ocn_pet_num = int(pet_nums_arr[-1]) - int(pet_nums_arr[0]) + 1 

      if 'coupling_interval_sec' in dic:
        dc2.update({'_coupling_interval_sec_' : dic['coupling_interval_sec']})

      if 'nems_configure' in dic:
        template = os.path.join(env.FIXnsem, 'templates', dic['nems_configure'])
        dest = os.path.join(env.COMIN, 'nems.configure')
        nems_conf = util.tmp2scr(filename=dest, tmpname=template, d=dc2)
        
    except Exception as e:
      print("Error: ",str(e))
      sys.exit(0)

    total_pets = ocn_pet_num + atm_pet_num + wav_pet_num
    
    # prepare model_configure
    sdate = env.start_date_str
    month=sdate[0:1]; day=sdate[3:4]; year=sdate[6:9]
    hour=sdate[11:12]; minute=sdate[4:5]; second=sdate[17:18] 
    dc={}
    dc.update({'start_year'     :year })
    dc.update({'start_month'    :month })
    dc.update({'start_day'      :day })
    dc.update({'start_hour'     :hour})
    dc.update({'start_minute'   :minute})
    dc.update({'start_second'   :second})
    dc.update({'nhours'         :str(env.frcst_hrs)})
    dc.update({'total_pets'     :str(total_pets)})
    #
    template = os.path.join(env.FIXnsem, 'templates', 'atm_namelist.rc.template')   #TODO check on this file, use model_configure
    dest = os.path.join(env.COMIN, 'model_configure')
    #model_configure  = os.path.join(run_dir,'atm_namelist.rc')
    model_conf = util.tmp2scr(filename=dest, tmpname=template, d=dc)
    #os.system('ln -svf ' + model_configure + ' ' + os.path.join(run_dir,'model_configure' ) )
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/')
    ##################################################################################



def prep_ww3(run_dir):
    """
    Prepare ww3 run files
    uses vars imported from base_info.py
   
    """
    #ww3
    txt1 = ' > Prepare ww3 inps ... (take couple of minutes)'
    logf(txt1,log_file)

    os.chdir(run_dir)

    # Process WW3 grid and physics
    txt1 = ' > Processing WW3 grid and physics...'
    logf(txt1,log_file)
    os.system('cp -f ' + ww3_grd_inp + '/*.msh ' + run_dir)
    os.system('cp -f ' + ww3_grd_inp + '/ww3_grid.inp ' + run_dir)
    os.system('${EXECnsem}/ww3_grid ww3_grid.inp > ww3_grid.out')
    os.system('cp -p mod_def.ww3 mod_def.inlet')
    os.system('cp -p mod_def.ww3 mod_def.points')

    if base_info.wbound_flg:
       # Process WW3 boundary conditions
       txt1 = ' > Processing WW3 boundary conditions...'
       logf(txt1,log_file)
       os.system('cp -f ${COMINwave}/*.spc ' + run_dir)
       os.system('cp -f ' + ww3_grd_inp + '/ww3_bound.inp ' + run_dir)
       os.system('${EXECnsem}/ww3_bound ww3_bound.inp > ww3_bound.out')
       os.system('mv nest.ww3 nest.inlet')
       os.system('${EXECnsem}/ww3_bound ww3_bound.inp > ww3_bound.out')
       os.system('mv nest.ww3 nest.inlet')  
    ##########
    dc_ww3_multi={}
    dc_ww3_multi.update({'start_pdy'    :base_info.tide_spin_end_date.strftime("%Y%m%d %H%M%S") })
    dc_ww3_multi.update({'end_pdy'      :base_info.wave_spin_end_date.strftime("%Y%m%d %H%M%S") })
    dc_ww3_multi.update({'dt_out_sec'   :3600  })
    ##
    tmpname = os.path.join(FIXnsem, 'templates', base_info.ww3_multi_tmpl)
    ww3_multi = os.path.join(run_dir,'ww3_multi.inp')
    util.tmp2scr(filename=ww3_multi,tmpname=tmpname,d=dc_ww3_multi)
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/') 


def prep_atm():
#    print ' > Prepare ' + base_info.atm_name
#    #os.system ('cp -r  '+  os.path.join(base_info.app_inp_dir,base_info.atm_inp_dir)  + '  ' + run_dir)



    #TODO: Only copy the forcing file not the whole directory

#def prep_wav():
#    print ' > Prepare ' + base_info.wav_name
#    os.system ('cp -r  '+  os.path.join(base_info.app_inp_dir,base_info.wav_inp_dir)  + '  ' + run_dir)


def prep_adc(dic):

    """
    adcirc preparation per storm and per run name requires:
    1) update model parameter and periodic boundary condition file (fort.15)
       a) copy adcprep executable
    2) copy adc-grd-input (i.e. ocn mesh)
    3) copy wave-grd-input (i.e. wav mesh)
    4) copy restart files, fort.67.nc, fort.68.nc
    5) copy tidefac - for which case?? 
    6) copy adc-input - what and where are these?
    7) pet nums - reason?
    8) copy atm files - which one?, do you need processing?
    9) dependencies: nems model_configure and nems.configure
                     spinup period 
    """
    
    msg = "\tUpdating boundary condition, fort15 ....."
    print(util.colory("green",msg))
    update_fort15(dic)
       
    # copy files that are needed 
    adcprep = os.path.join(env.EXECnsem, 'adcprep')
    
    """
    fort15  = os.path.join(run_dir,'fort.15')  #copy after update_fort15
    adcprep   = os.path.join(EXECnsem, 'adcprep')
    tidefac   = os.path.join(EXECnsem, 'tidefac')
    # adc_inp   = os.path.join(COMINadc) # this must be copied there manually by HYDRO_STREAM, see CONOPS7
    adc_grd_inp   = os.path.join(FIXnsem,'meshes',storm,'ocn')  # copy HSOFS grid similar for all cases
    ww3_grd_inp   = os.path.join(FIXnsem,'meshes',storm,'wav')
    hot_file = os.path.join(GESIN,'hotfiles','fort.67.nc')  # TODO once manual next after running tide_spinup??
    os.system('cp -f ' + hot_file +' ' + run_dir)
    hot_file = os.path.join(GESIN,'hotfiles','fort.68.nc')        
    os.system('cp -f ' + hot_file +' ' + run_dir)
    """


    # $COMROOT/$NET/$envir/$RUN.$PDY
    target = env.COMINadc
    try:
        shutil.copy(adcprep, target)
    except IOError as e:
        print("\nUnable to copy file. %s" % e)
    except:
        print("\nUnexpected error:", sys.exc_info())
    


def prep_ww3(run_dir):
    """
    Prepare ww3 run files
    uses vars imported from base_info.py
   
    """
    #ww3
    txt1 = ' > Prepare ww3 inps ... (take couple of minutes)'
    #logf(txt1,log_file) 

    os.chdir(run_dir)

    # Process WW3 grid and physics
    txt1 = ' > Processing WW3 grid and physics...'
    #logf(txt1,log_file) 
    os.system('cp -f ' + ww3_grd_inp + '/*.msh ' + run_dir)
    os.system('cp -f ' + ww3_grd_inp + '/ww3_grid.inp ' + run_dir)
    os.system('${EXECnsem}/ww3_grid ww3_grid.inp > ww3_grid.out')
    os.system('cp -p mod_def.ww3 mod_def.inlet')
    os.system('cp -p mod_def.ww3 mod_def.points')

    if base_info.wbound_flg:
       # Process WW3 boundary conditions
       txt1 = ' > Processing WW3 boundary conditions...'
       #logf(txt1,log_file) 
       os.system('cp -f ${COMINwave}/*.spc ' + run_dir)
       os.system('cp -f ' + ww3_grd_inp + '/ww3_bound.inp ' + run_dir)
       os.system('${EXECnsem}/ww3_bound ww3_bound.inp > ww3_bound.out')
       os.system('mv nest.ww3 nest.inlet')  
    ##########
    dc_ww3_multi={}
    dc_ww3_multi.update({'start_pdy'    :base_info.tide_spin_end_date.strftime("%Y%m%d %H%M%S") })
    dc_ww3_multi.update({'end_pdy'      :base_info.wave_spin_end_date.strftime("%Y%m%d %H%M%S") })
    dc_ww3_multi.update({'dt_out_sec'   :3600  })
    ##
    tmpname = os.path.join(FIXnsem, 'templates', base_info.ww3_multi_tmpl)
    ww3_multi = os.path.join(run_dir,'ww3_multi.inp')
    util.tmp2scr(filename=ww3_multi,tmpname=tmpname,d=dc_ww3_multi)
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/') 



def rprep_nems(run_dir):
    """ Preapre nems run time files """ 
   
    # model_configure

    # nems.configure

    # build.sh

    # slurm.job

    # NEMS.x
    #print ' > Prepare NEMS related input files ..'
    txt1 = ' > Prepare NEMS related input files ..'
    #logf(txt1,log_file)     
    # NEMS.x
    os.system ('cp -f ' + nems_exe + ' ' + run_dir)    

    #   
    ocn_pet_num = 0
    atm_pet_num = 0
    wav_pet_num = 0

    dc2={}
    dc2.update({'c'  :'#' })
    if base_info.ocn_name is not None:
        dc2.update({'_ocn_model_'          : base_info.ocn_name    })
        dc2.update({'_ocn_petlist_bounds_' : base_info.ocn_petlist })
        pet_nums = np.int_ (np.array(base_info.ocn_petlist.split()))
        ocn_pet_num = pet_nums[-1] - pet_nums[0] + 1 

    if base_info.atm_name is not None:
        dc2.update({'_atm_model_'          : base_info.atm_name    })
        dc2.update({'_atm_petlist_bounds_' : base_info.atm_petlist })
        pet_nums = np.int_ (np.array(base_info.atm_petlist.split()))
        atm_pet_num = pet_nums[-1] - pet_nums[0] + 1 

    if base_info.wav_name is not None:
        dc2.update({'_wav_model_'          : base_info.wav_name    })
        dc2.update({'_wav_petlist_bounds_' : base_info.wav_petlist })
        pet_nums = np.int_ (np.array(base_info.wav_petlist.split()))
        wav_pet_num = pet_nums[-1] - pet_nums[0] + 1 

    if base_info.coupling_interval_sec is not None:
        dc2.update({'_coupling_interval_sec_' : base_info.coupling_interval_sec    })

    #if base_info.coupling_interval_slow_sec is not None:
    #    dc2.update({'_coupling_interval_slow_sec_' : base_info.coupling_interval_slow_sec    })

    #if base_info.coupling_interval_fast_sec is not None:
    #    dc2.update({'_coupling_interval_fast_sec_' : base_info.coupling_interval_fast_sec    })

    txt1 = '   > Prepare atm_namelist.rc ..'
    #logf(txt1,log_file)   
    
    total_pets = ocn_pet_num + atm_pet_num + wav_pet_num
    tmpname = os.path.join(PARMnsem, base_info.nems_configure)
    model_configure  = os.path.join(run_dir,'nems.configure')
    util.tmp2scr(filename=model_configure,tmpname=tmpname,d=dc2)
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/')
    ##########
    dc={}
    dc.update({'start_year'     :base_info.start_date_nems.year    })
    dc.update({'start_month'    :base_info.start_date_nems.month   })
    dc.update({'start_day'      :base_info.start_date_nems.day     })
    dc.update({'start_hour'     :base_info.start_date_nems.hour    })
    dc.update({'start_minute'   :base_info.start_date_nems.minute  })
    dc.update({'start_second'   :base_info.start_date_nems.second  })
    dc.update({'nhours'         :str(base_info.ndays * 24)})
    dc.update({'total_pets'     :str(total_pets)})
    ##
    tmpname = os.path.join(FIXnsem, 'templates', base_info.model_configure)
    model_configure  = os.path.join(run_dir,'atm_namelist.rc')
    util.tmp2scr(filename=model_configure,tmpname=tmpname,d=dc)
    os.system('ln -svf ' + model_configure + ' ' + os.path.join(run_dir,'model_configure' ) )
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/')
    ##################################################################################
    txt1 = '   > Prepare nems.configure ..'
    #logf(txt1,log_file)   
    
    pet_max = 0
    dc3={}
    dc3.update({'c'  :'#' })
    if base_info.ocn_name is not None:
        dc3.update({'_ocn_model_'          : base_info.ocn_name    })
        dc3.update({'_ocn_petlist_bounds_' : base_info.ocn_petlist })
        pet_nums = np.int_ (np.array(base_info.ocn_petlist.split()))
        ocn_pet_num = pet_nums[-1] - pet_nums[0] + 1 
        pet_max = max(pet_nums[0],pet_nums[-1])

    if base_info.atm_name is not None:
        dc3.update({'_atm_model_'          : base_info.atm_name    })
        dc3.update({'_atm_petlist_bounds_' : base_info.atm_petlist })
        pet_nums = np.int_ (np.array(base_info.atm_petlist.split()))
        atm_pet_num = pet_nums[-1] - pet_nums[0] + 1 
        pet_max = max(pet_max,pet_nums[0],pet_nums[-1])

    if base_info.wav_name is not None:
        dc3.update({'_wav_model_'          : base_info.wav_name    })
        dc3.update({'_wav_petlist_bounds_' : base_info.wav_petlist })
        pet_nums = np.int_ (np.array(base_info.wav_petlist.split()))
        wav_pet_num = pet_nums[-1] - pet_nums[0] + 1 
        pet_max = max(pet_max,pet_nums[0],pet_nums[-1])

    if base_info.coupling_interval_sec is not None:
        dc3.update({'_coupling_interval_sec_' : base_info.coupling_interval_sec    })

    #if base_info.coupling_interval_slow_sec is not None:
    #    dc3.update({'_coupling_interval_slow_sec_' : base_info.coupling_interval_slow_sec    })

    #if base_info.coupling_interval_fast_sec is not None:
    #    dc3.update({'_coupling_interval_fast_sec_' : base_info.coupling_interval_fast_sec    })

    #total_pets = ocn_pet_num + atm_pet_num + wav_pet_num
    total_pets = pet_max + 1
    tmpname = os.path.join(PARMnsem, base_info.nems_configure)
    model_configure  = os.path.join(run_dir,'nems.configure')
    util.tmp2scr(filename=model_configure,tmpname=tmpname,d=dc3)
    #os.system('cp -fr  ' +   tmpname          +'  '   +run_dir+'/scr/')

    txt1 = '   > Prepare config.rc ..'
    #logf(txt1,log_file)   
    
    #generate apps.rc file
    apps_conf = os.path.join(run_dir,'config.rc')
    
    if base_info.wav_name == 'ww3data':
        #wav_dir   = os.path.join(run_dir, os.path.normpath(base_info.wav_inp_dir).split('/')[-1])
        wav_dir = COMINwave
        os.system ('echo " wav_dir: ' +  wav_dir                        + ' " >> ' + apps_conf )
        os.system ('echo " wav_nam: ' +  base_info.wav_netcdf_file_name + ' " >> ' + apps_conf )
        #
        wav_inp_file    = os.path.join(COMINwave,base_info.wav_netcdf_file_name)
        wav_rundir_file = os.path.join(wav_dir,base_info.wav_netcdf_file_name)
        if True:
            txt1 =  '  > Link Wave Inp ...'
            #logf(txt1,log_file)             
            
            os.system ('mkdir -p  ' +  wav_dir                                   )
            os.system ('ln    -sf ' +  wav_inp_file + ' ' + wav_rundir_file      )
        else:        
            #print '  > Copy Wave Inp ...'
            txt1 = '  > Copy WAV Inp ...'
            #logf(txt1,log_file)             
            
            os.system ('mkdir -p  ' +  wav_dir                                   )
            os.system ('cp    -f  ' +  wav_inp_file + ' ' + wav_rundir_file      )

    if base_info.atm_name is not None:
        #atm_dir   = os.path.join(run_dir, os.path.normpath(base_info.atm_inp_dir).split('/')[-1])
        atm_dir = COMINatm
        os.system ('echo " atm_dir: ' +  atm_dir                        + ' " >> ' + apps_conf )
        os.system ('echo " atm_nam: ' +  base_info.atm_netcdf_file_name + ' " >> ' + apps_conf )
        #
        atm_inp_file    = os.path.join(COMINatm,base_info.atm_netcdf_file_name)
        atm_rundir_file = os.path.join(atm_dir,base_info.atm_netcdf_file_name)
        if True:
            txt1 =  '  > Link ATM Inp ...'
            #logf(txt1,log_file)             
            
            os.system ('mkdir -p  ' +  atm_dir                                   )
            os.system ('ln    -sf ' +  atm_inp_file + ' ' + atm_rundir_file      )
        else:
            #print '  > Copy ATM Inp ...'  
            txt1 = '  > Copy ATM Inp ...'
            #logf(txt1,log_file)                  
            os.system ('mkdir -p  ' +  atm_dir                                   )
            os.system ('cp    -f  ' +  atm_inp_file + ' ' + atm_rundir_file      )               



def get_tidal_fact(run_dir):
    """
    based on spin-up start time prepare tide fac to be used in fort.15.tempelate
    In:
    Out: tidal fact dictionary
    
    """
    
    duration = str ((base_info.wave_spin_end_date-base_info.tide_spin_start_date).total_seconds() /86400.)
    

    # copy tidal input file
    os.system('cp -f ' + PARMnsem + '/storms/' + STORM + '/tide_inp.txt ' + run_dir)

    tidefac_inp_file = os.path.join(run_dir, 'tide_inp.txt')
    tidefac_inp      = open(tidefac_inp_file,'w')
    # write data
    tidefac_inp.write( duration + ' \n')  #for 1 year
    tidefac_inp.write(str(base_info.tide_spin_start_date.hour) +' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.day)  +' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.month)+' ')
    tidefac_inp.write(str(base_info.tide_spin_start_date.year) +' ')
    tidefac_inp.close()
       
    #comm0 = "source " + modfile +' ; '
    comm1  = ' cd   ' + run_dir + ' ; '+tidefac +' <  tide_inp.txt  >  tidefac.log'
    #print(comm1)
    
    txt1 = comm1
    #logf(txt1,log_file)      
    
    os.system(comm1)
    
    tidefac_dic = {}
    tidefac_out_file = os.path.join(run_dir, 'tide_fac.out')
    tidefac_out      = open(tidefac_out_file,'r')
    
    for line in tidefac_out.readlines():
        params = line.split()
        print(line)
        if 'K1'  in  params:    fft1,facet1   = params[1],params[2]
        if 'O1'  in  params:    fft2,facet2   = params[1],params[2]
        if 'P1'  in  params:    fft3,facet3   = params[1],params[2]
        if 'Q1'  in  params:    fft4,facet4   = params[1],params[2]
        if 'N2'  in  params:    fft5,facet5   = params[1],params[2]
        if 'M2'  in  params:    fft6,facet6   = params[1],params[2]
        if 'S2'  in  params:    fft7,facet7   = params[1],params[2]
        if 'K2'  in  params:    fft8,facet8   = params[1],params[2]
        if 'MF'  in  params:    fft9,facet9   = params[1],params[2]
        if 'MM'  in  params:    fft10,facet10 = params[1],params[2]
        if 'M4'  in  params:    fft11,facet11 = params[1],params[2]
        if 'MS4' in  params:    fft12,facet12 = params[1],params[2]
        if 'MN4' in  params:    fft13,facet13 = params[1],params[2]
    tidefac_out.close()
    return dict ( fft1=fft1,facet1=facet1,   
                  fft2=fft2,facet2=facet2,   
                  fft3=fft3,facet3=facet3,   
                  fft4=fft4,facet4=facet4,   
                  fft5=fft5,facet5=facet5,   
                  fft6=fft6,facet6=facet6,   
                  fft7=fft7,facet7=facet7,   
                  fft8=fft8,facet8=facet8,   
                  fft9=fft9,facet9=facet9,   
                  fft10=fft10,facet10=facet10, 
                  fft11=fft11,facet11=facet11, 
                  fft12=fft12,facet12=facet12, 
                  fft13=fft13,facet13=facet13) 

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

def change_nws():
    """
    Go through all fort.15 files and change nws. I need
    this routine because adcprep still not addapted to handl nws=17.
  
    
    """
    import glob
    
    sys.exit( 'Fixed internally. Go ahead and chenge your main fort.15 if needed!')
      
    pattern = 'NWS'   
    nws     = str (base_info.nws)
    line2replace  = ' ' +nws+ \
        '                                       ! NWS - WIND STRESS AND BAROMETRIC PRESSURE \n'
    #replace main fort.15
    filename = os.path.join(run_dir,'fort.15')
    replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )

    #replace fort.15 in PE directories

    dirs = glob.glob(run_dir + '/PE0*')
    
    for dir1 in dirs:
         filename = os.path.join(dir1,'fort.15')
         replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )  
    
    print(' > Finished updating  fort.15s')
    
    #####
    pattern = 'NWS'   
    nws     = str (base_info.nws)
    line2replace  = '       ' + nws + \
        '                        ! NWS, wind data type \n'
    filename = os.path.join(run_dir,'fort.80')
    replace_pattern_line( filename = filename , pattern = pattern, line2replace = line2replace )
    print(' > Finished updating  fort.80')
   
def back_up_codes(run_dir):
    #cap_dir  = os.path.join(base_info.application_dir, 'ADCIRC_CAP' )        
    ocn_dir  = os.path.join(base_info.application_dir, 'ADCIRC' )            
    nem_dir  = os.path.join(base_info.application_dir, 'NEMS' )            
    #   
    #os.system('tar -zcf '+run_dir+'/scr/ADCIRC_CAP.tgz '+ cap_dir)
    os.system('tar -zcf '+run_dir+'/scr/ADCIRC.tgz '    + ocn_dir)
    os.system('tar -zcf '+run_dir+'/scr/NEMS.tgz '      + nem_dir)
    #print ' > Finished backing up codes'

    txt1 = ' > Finished backing up codes ..'
    #logf(txt1,log_file)      

def plot_domain_decomp(run_dir):
    import pynmd.models.adcirc.post as adcp 
    import pynmd.plotting.plot_settings as ps
    import matplotlib.pyplot as plt
    decomps = adcp.ReadFort80(run_dir+'/')
    nproc = decomps['nproc']
    IMAP_NOD_LG = decomps['IMAP_NOD_LG'] 
    IMAP_EL_LG  = decomps['IMAP_EL_LG'] 
    IMAP_NOD_GL = decomps['IMAP_NOD_GL']
    x,y,tri = adcp.ReadTri  (run_dir+'/')
     
    fig = plt.figure(figsize=(5,5))
    ax  =  fig.add_subplot(111)
    xp  = []
    yp  = []
    cc = 100 * ps.colors
    mm = 100 * ps.marker
    for ip in range(nproc):
        ind = np.where(IMAP_NOD_GL[:,1] == ip)
        ind = ind[::10]
        ax.scatter(tri.x[ind],tri.y[ind], c = cc[ip],
            s = 0.2 , edgecolors = 'None', marker = mm[ip])
    fig.savefig(run_dir + '/0decomp.png',dpi=450)
    plt.close()
    #print ' > Finished plotting domain decomposition'
    txt1 = ' > Finished plotting domain decomposition ..'
########
def one_run_eq():
    run_dir = RUNdir
    #os.system('echo "cd  ' + run_dir +' " >> ' + run_scr )
    #os.system('echo "qsub qsub.sh      " >> ' + run_scr )
    #os.system('echo "sbatch slurm.sh    " >> ' + run_scr )
    #
    prep_nems(run_dir)
    prep_adc()
    if base_info.run_option == 'atm2wav2ocn': 
       prep_ww3(run_dir) 

    if False:
        plot_domain_decomp(run_dir)
        back_up_codes(run_dir)



def main():

    # these are being set before prep_adc is called
    spin_time()
    adc_atm_data(env.storm,"hwrf")
    adc_wave_data(env.storm,"hwrf")

    msg = "\nFinished preparing data for NSEM\n"
    print(util.colory("blue", msg))


if __name__ == '__main__':
    read_ini()
    sys.exit(0)
    main()
