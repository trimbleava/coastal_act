#!/usr/bin/env python

"""
File Name   : func_nsem_prep.py
Description : NSEM models data preparation
Usage       : Import this into an external python program such as main.py (i.e. import func_nsem_prep)
Date        : 7/6/2020
Contacts    : Coastal Act Team 
              ali.abdolali@noaa.gov, saeed.moghimi@noaa.gov, beheen.m.trimble@gmail.com, andre.vanderwesthuysen@noaa.gov
"""

import os, sys
import subprocess, shutil
from pathlib import Path

# local
import func_nsem_workflow as fnw
import nsem_utils as nus


class NWM():
    def __init__(self, ini, start_date_str, duration_hours):

        self.start_date_str = start_date_str                            # yyyy-mm-dd hh:mm:ss
        self.duration_hours = duration_hours                            # how long model to run per storm, used in name construction here
        self.data_path = ini.NWM['nwm_data_path']                       # standalone location of NWM input files
        self.storm = ini.STORM.lower()                                  # storm name is built into standalone nwm directory structure
                                                                        # and it is in lower case. Make sure it is defined as such in
                                                                        # the initialization file (nsem_ini.py).
        # calculated variables
        duration_day = int(self.duration_hours / 24)                    # for nwm file name construction
        start_date = nus.to_date(start_date_str, 1)                     # for nwm file name construction

        #
        self.domain = ini.NWM['domain']                                 # domain value is built into standalone nwm directory structure
                                                                        # such as CONUS, Gulf, Atlantic, Base, ...
        # runtime location of NWM input files, excluding the path
        self.comin_nwm = ini.COMINnwm                                   

        # domain files
        self.domain_files = ini.NWM['domain_files']                     # nwm spatial input files, domain files

        forcing_files = ini.NWM['forcing_files']                        # nwm forcing files are in this format: yyyymmddhh.LDASIN_DOMAIN1
        fs0 = forcing_files[0]                                          # all such files are defined in initialization file like a template. 
        #forcing_files[0] = fs0.replace('yyyymmddhh',self.start_date.strftime("%Y%m%d%H"))
        self.forcing_files = []
        # rebuilding forcing file format to actual forcing files (2016100100, 2016100101, ...) - number of files are depend on length of storm
        for this_date in nus.dateloop_byhour(start_date, self.duration_hours):
            self.forcing_files.append(fs0.replace('yyyymmddhh',this_date.strftime("%Y%m%d%H")))
           
        # restart template filenames to actual restart filenames 
        self.restart_files = ini.NWM['restart_files']  
        rs0 = self.restart_files['hydro']
        self.restart_files['hydro'] = rs0.replace('yyyy-mm-dd',start_date.strftime("%Y-%m-%d"))            # 'HYDRO_RST.yyyy-mm-dd_00_00_DOMAIN1'
        rs1 = self.restart_files['restart']
        self.restart_files['restart'] = rs1.replace('yyyymmddhh',start_date.strftime("%Y%m%d%H"))          # 'RESTART.yyyymmddhh_DOMAIN1'
        rs2 = self.restart_files['nudginglastobs']
        self.restart_files['nudginglastobs'] = rs2.replace('yyyy-mm-dd',start_date.strftime("%Y-%m-%d"))   # 'nudgingLastObs.yyyy-mm-dd_00_00_00.nc'

        # timeslice template to actual timeslices files - number of files are depend on length of storm
        self.discharge_obs_files = ini.NWM['nudgingTimeSliceObs_files']  # template format: yyyy-mm-dd_hh:mm:ss.15min.usgsTimeSlice.ncdf
        obs0 = self.discharge_obs_files[0]
        self.discharge_obs_files[0] = obs0.replace('yyyy-mm-dd_hh:mm', start_date.strftime("%Y-%m-%d_00:00"))
        # rebuilding nudging file format to actual nudging files (2016-10-01_00:00, 2016-10-01_01:15, ...) 
        # number of files are depend on length of storm
        for this_date in nus.dateloop_15min(start_date, self.duration_hours*60):
            self.discharge_obs_files.append(obs0.replace('yyyy-mm-dd_hh:mm',this_date.strftime("%Y-%m-%d_%H:%M")))
         
        # expected to be located in nwm standalone data directory
        self.config_files = ini.NWM['config_files']
        self.table_files = ini.NWM['table_files']



    def check_configs(self,ini):
      
        namelist_cfg = self.config_files['namelist']   # namelist.hrldas
        namelist_cfg = "namelist.hrldas_comp" # in testing phase - to decide to copy or to create!!

        print("\nConstructing %s configuration file" %namelist_cfg)

        lines = """&NOAHLSM_OFFLINE

HRLDAS_SETUP_FILE = "{}"   
INDIR = "{}"               
SPATIAL_FILENAME = "{}"
OUTDIR = "./"
START_YEAR  = {}    
START_MONTH = {}   
START_DAY   = {}  
START_HOUR  = {} 
START_MIN   = {}

! Specification of the land surface model restart file
! Comment out the option if not initializing from a restart file
RESTART_FILENAME_REQUESTED = "{}"

! Specification of simulation length in hours 
! KDAY = 7 ! This option is deprecated and may be removed in a future version
KHOUR = {} 

! Physics options (see the documentation for details)
DYNAMIC_VEG_OPTION                = 4
CANOPY_STOMATAL_RESISTANCE_OPTION = 1
BTR_OPTION                        = 1
RUNOFF_OPTION                     = 3
SURFACE_DRAG_OPTION               = 1
FROZEN_SOIL_OPTION                = 1
SUPERCOOLED_WATER_OPTION          = 1
RADIATIVE_TRANSFER_OPTION         = 3
SNOW_ALBEDO_OPTION                = 2
PCP_PARTITION_OPTION              = 1
TBOT_OPTION                       = 2
TEMP_TIME_SCHEME_OPTION           = 3
GLACIER_OPTION                    = 2
SURFACE_RESISTANCE_OPTION         = 4

! Timesteps in units of seconds
FORCING_TIMESTEP = 3600
NOAH_TIMESTEP    = 3600
OUTPUT_TIMESTEP  = 3600

! Land surface model restart file write frequency
! A value of -99999 will output restarts on the first day of the month only
RESTART_FREQUENCY_HOURS = 24

! Split output after split_output_count output times.
SPLIT_OUTPUT_COUNT = 1

! Soil layer specification
NSOIL=4
soil_thick_input(1) = 0.10
soil_thick_input(2) = 0.30
soil_thick_input(3) = 0.60
soil_thick_input(4) = 1.00

! Forcing data measurement height for winds, temp, humidity
ZLVL = 10.0

! Restart file format options
rst_bi_in = 0      !0: use netcdf input restart file
                   !1: use parallel io for reading multiple restart files (1 per core)
rst_bi_out = 0     !0: use netcdf output restart file
                   !1: use parallel io for outputting multiple restart files (1 per core)

/

&WRF_HYDRO_OFFLINE

! Specification of forcing data:  1=HRLDAS-hr format, 2=HRLDAS-min format, 3=WRF,
!    4=Idealized, 5=Idealized w/ spec. precip.,
!    6=HRLDAS-hr format w/ spec. precip., 7=WRF w/ spec. precip.,
!    9=Channel-only forcing, see hydro.namelist output_channelBucket_influxes
!    10=Channel+Bucket only forcing, see hydro.namelist output_channelBucket_influxes
FORC_TYP = 1

/
""".format(os.path.join("domain", self.domain, self.domain_files['wrfinput']), 
           "forcing/", 
           os.path.join("domain", self.domain, self.domain_files['soilprop']),
           ini.model_configure['start_year'], ini.model_configure['start_month'], 
           ini.model_configure['start_day'], ini.model_configure['start_hour'], ini.model_configure['start_minute'],
           os.path.join("restart",self.storm, self.restart_files['restart']), 
           self.duration_hours,
          ) 

        cf = os.path.join(self.comin_nwm,namelist_cfg) 
        with open(cf, 'w+') as f:
            f.write(lines)


        # create hydro config now
        hydro_cfg = self.config_files['hydro']      # hydro.namelist
        hydro_cfg = "hydro.namelist_comp"     # in testing phase to decide if to use copy or to create
        print("\nConstructing %s configuration file" %hydro_cfg)

        lines = """
&HYDRO_nlist
!!!! ---------------------- SYSTEM COUPLING ----------------------- !!!!

! Specify what is being coupled:  1=HRLDAS (offline Noah-LSM), 2=WRF, 3=NASA/LIS, 4=CLM
sys_cpl = 1

!!!! ------------------- MODEL INPUT DATA FILES ------------------- !!!!

! Specify land surface model gridded input data file (e.g.: "geo_em.d01.nc")
GEO_STATIC_FLNM = "{}"     

! Specify the high-resolution routing terrain input data file (e.g.: "Fulldom_hires.nc")
GEO_FINEGRID_FLNM = "{}"

! Specify the spatial hydro parameters file (e.g.: "hydro2dtbl.nc")
! If you specify a filename and the file does not exist, it will be created for you.
HYDROTBL_F = "{}"

! Specify spatial metadata file for land surface grid. (e.g.: "GEOGRID_LDASOUT_Spatial_Metadata.nc")
LAND_SPATIAL_META_FLNM = "{}"

! Specify the name of the restart file if starting from restart...comment out with '!' if not...
RESTART_FILE  = '{}'

!!!! --------------------- MODEL SETUP OPTIONS -------------------- !!!!

! Specify the domain or nest number identifier...(integer)
IGRID = 1

! Specify the restart file write frequency...(minutes)
! A value of -99999 will output restarts on the first day of the month only.
rst_dt = 120

! Reset the LSM soil states from the high-res routing restart file (1=overwrite, 0=no overwrite)
! NOTE: Only turn this option on if overland or subsurface rotuing is active!
rst_typ = 1

! Restart file format control
rst_bi_in = 0       !0: use netcdf input restart file (default)
                    !1: use parallel io for reading multiple restart files, 1 per core
rst_bi_out = 0      !0: use netcdf output restart file (default)
                    !1: use parallel io for outputting multiple restart files, 1 per core

! Restart switch to set restart accumulation variables to 0 (0=no reset, 1=yes reset to 0.0)
RSTRT_SWC = 0

! Specify baseflow/bucket model initialization...(0=cold start from table, 1=restart file)
GW_RESTART = 1

!!!! -------------------- MODEL OUTPUT CONTROL -------------------- !!!!

! Specify the output file write frequency...(minutes)
out_dt = 60

! Specify the number of output times to be contained within each output history file...(integer)
!   SET = 1 WHEN RUNNING CHANNEL ROUTING ONLY/CALIBRATION SIMS!!!
!   SET = 1 WHEN RUNNING COUPLED TO WRF!!!
SPLIT_OUTPUT_COUNT = 1

! Specify the minimum stream order to output to netcdf point file...(integer)
! Note: lower value of stream order produces more output.
order_to_write = 1

! Flag to turn on/off new I/O routines: 0 = deprecated output routines (use when running with Noah LSM),
! 1 = with scale/offset/compression, ! 2 = with scale/offset/NO compression,
! 3 = compression only, 4 = no scale/offset/compression (default)
io_form_outputs = 4

! Realtime run configuration option:
! 0=all (default), 1=analysis, 2=short-range, 3=medium-range, 4=long-range, 5=retrospective,
! 6=diagnostic (includes all of 1-4 outputs combined)
io_config_outputs = 0

! Option to write output files at time 0 (restart cold start time): 0=no, 1=yes (default)
t0OutputFlag = 1

! Options to output channel & bucket influxes. Only active for UDMP_OPT=1.
! Nonzero choice requires that out_dt above matches NOAH_TIMESTEP in namelist.hrldas.
! 0=None (default), 1=channel influxes (qSfcLatRunoff, qBucket)
! 2=channel+bucket fluxes    (qSfcLatRunoff, qBucket, qBtmVertRunoff_toBucket)
! 3=channel accumulations    (accSfcLatRunoff, accBucket) *** NOT TESTED ***
output_channelBucket_influx = 0

! Output netcdf file control
CHRTOUT_DOMAIN = 1           ! Netcdf point timeseries output at all channel points (1d)
                             !      0 = no output, 1 = output
CHANOBS_DOMAIN = 0           ! Netcdf point timeseries at forecast points or gage points (defined in Routelink)
                             !      0 = no output, 1 = output at forecast points or gage points.
CHRTOUT_GRID = 0             ! Netcdf grid of channel streamflow values (2d)
                             !      0 = no output, 1 = output
                             !      NOTE: Not available with reach-based routing
LSMOUT_DOMAIN = 0            ! Netcdf grid of variables passed between LSM and routing components (2d)
                             !      0 = no output, 1 = output
                             !      NOTE: No scale_factor/add_offset available
RTOUT_DOMAIN = 1             ! Netcdf grid of terrain routing variables on routing grid (2d)
                             !      0 = no output, 1 = output
output_gw = 1                ! Netcdf GW output
                             !      0 = no output, 1 = output
outlake  = 1                 ! Netcdf grid of lake values (1d)
                             !      0 = no output, 1 = output
frxst_pts_out = 0            ! ASCII text file of forecast points or gage points (defined in Routelink)
                             !      0 = no output, 1 = output

!!!! ------------ PHYSICS OPTIONS AND RELATED SETTINGS ------------ !!!!

! Specify the number of soil layers (integer) and the depth of the bottom of each layer... (meters)
! Notes: In Version 1 of WRF-Hydro these must be the same as in the namelist.input file.
!      Future versions will permit this to be different.
NSOIL=4
ZSOIL8(1) = -0.10
ZSOIL8(2) = -0.40
ZSOIL8(3) = -1.00
ZSOIL8(4) = -2.00

! Specify the grid spacing of the terrain routing grid...(meters)
DXRT = 250.0

! Specify the integer multiple between the land model grid and the terrain routing grid...(integer)
AGGFACTRT = 4

! Specify the channel routing model timestep...(seconds)
DTRT_CH = 10

! Specify the terrain routing model timestep...(seconds)
DTRT_TER = 10

! Switch to activate subsurface routing...(0=no, 1=yes)
SUBRTSWCRT = 1

! Switch to activate surface overland flow routing...(0=no, 1=yes)
OVRTSWCRT = 1

! Specify overland flow routing option: 1=Seepest Descent (D8) 2=CASC2D (not active)
! NOTE: Currently subsurface flow is only steepest descent
rt_option = 1

! Switch to activate channel routing...(0=no, 1=yes)
CHANRTSWCRT = 1

! Specify channel routing option: 1=Muskingam-reach, 2=Musk.-Cunge-reach, 3=Diff.Wave-gridded
channel_option = 1

! Specify the reach file for reach-based routing options (e.g.: "Route_Link.nc")
route_link_f = "{}"

! If using channel_option=2, activate the compound channel formulation? (Default=.FALSE.)
! This option is currently only supported if using reach-based routing with UDMP=1.
compound_channel = .FALSE.

! Specify the lake parameter file (e.g.: "LAKEPARM.nc").
! Note REQUIRED if lakes are on.
route_lake_f = "{}"

! Specify the reservoir parameter file
!reservoir_parameter_file = "./DOMAIN/persistence_parm.nc"

! If using USGS persistence reservoirs, set to True. (default=.FALSE.)
reservoir_persistence_usgs = .FALSE.

! Specify the path to the timeslice files to be used by USGS reservoirs
!reservoir_usgs_timeslice_path = "./usgs_timeslices/"

! If using USACE persistence reservoirs, set to True. (default=.FALSE.)
reservoir_persistence_usace = .FALSE.

! Specify the path to the timeslice files to be used by USACE reservoirs
!reservoir_usace_timeslice_path = "./usace_timeslices/"

! Specify lookback hours to read reservoir observation data
!reservoir_observation_lookback_hours = 24

! Specify update time interval in seconds to read new reservoir observation data
! The default is 86400 (seconds per day). Set to 3600 for standard and extended AnA simulations.
! Set to 1000000000 for short range and medium range forecasts.
!reservoir_observation_update_time_interval_seconds = 3600

! If using RFC forecast reservoirs, set to True. (default=.FALSE.)
reservoir_rfc_forecasts = .FALSE.

! Specify the path to the RFC time series files to be used by reservoirs
!reservoir_rfc_forecasts_time_series_path = "./rfc_timeseries/"

! Specify lookback hours to read reservoir RFC forecasts
!reservoir_rfc_forecasts_lookback_hours = 28

! Switch to activate baseflow bucket model...(0=none, 1=exp. bucket, 2=pass-through,
! 4=exp. bucket with area normalized parameters)
! Option 4 is currently only supported if using reach-based routing with UDMP=1.
GWBASESWCRT = 1

! Switch to activate bucket model loss (0=no, 1=yes)
! This option is currently only supported if using reach-based routing with UDMP=1.
bucket_loss = 0

! Groundwater/baseflow 2d mask specified on land surface model grid (e.g.: "GWBASINS.nc")
! Note: Only required if baseflow  model is active (1 or 2) and UDMP_OPT=0.
!gwbasmskfil = "./DOMAIN/GWBASINS.nc"

! Groundwater bucket parameter file (e.g.: "GWBUCKPARM.nc")
GWBUCKPARM_file = "{}"

! User defined mapping, such as NHDPlus: 0=no (default), 1=yes
UDMP_OPT = 0

! If on, specify the user-defined mapping file (e.g.: "spatialweights.nc")
!udmap_file = "{}"

/

&NUDGING_nlist

! Path to the "timeslice" observation files.
timeSlicePath = "{}"

nudgingParamFile = "{}"

! Nudging restart file = "nudgingLastObsFile"
! nudgingLastObsFile defaults to '', which will look for nudgingLastObs.YYYY-mm-dd_HH:MM:SS.nc
!   **AT THE INITALIZATION TIME OF THE RUN**. Set to a missing file to use no restart.
!nudgingLastObsFile = '/a/nonexistent/file/gives/nudging/cold/start'
nudgingLastObsFile = "{}"

!! Parallel input of nudging timeslice observation files?
readTimesliceParallel = .TRUE.

! temporalPersistence defaults to true, only runs if necessary params present.
temporalPersistence = .FALSE.

! The total number of last (obs, modeled) pairs to save in nudgingLastObs for
! removal of bias. This is the maximum array length. (This option is active when persistBias=FALSE)
! (Default=960=10days @15min obs resolution, if all the obs are present and longer if not.)
nLastObs = {}

! If using temporalPersistence the last observation persists by default.
! This option instead persists the bias after the last observation.
persistBias = .FALSE.

! AnA (FALSE)  vs Forecast (TRUE) bias persistence.
! If persistBias: Does the window for calculating the bias end at
! model init time (=t0)?
! FALSE = window ends at model time (moving),
! TRUE = window ends at init=t0(fcst) time.
! (If commented out, Default=FALSE)
! Note: Perfect restart tests require this option to be .FALSE.
biasWindowBeforeT0 = .FALSE.

! If persistBias: Only use this many last (obs, modeled) pairs. (If Commented out, Default=-1*nLastObs)
! > 0: apply an age-based filter, units=hours.
! = 0: apply no additional filter, use all available/usable obs.
! < 0: apply an count-based filter, units=count
maxAgePairsBiasPersist = -960

! If persistBias: The minimum number of last (obs, modeled) pairs, with age less than
! maxAgePairsBiasPersist, required to apply a bias correction. (default=8)
minNumPairsBiasPersist = 8

! If persistBias: give more weight to observations closer in time? (default=FALSE)
invDistTimeWeightBias = .TRUE.

! If persistBias: "No constructive interference in bias correction?", Reduce the bias adjustment
! when the model and the bias adjustment have the same sign relative to the modeled flow at t0?
! (default=FALSE)
! Note: Perfect restart tests require this option to be .FALSE.
noConstInterfBias = .FALSE.

/

""".format(os.path.join("domain",self.domain, self.domain_files['geom']),
           os.path.join("domain",self.domain,self.domain_files['fulldom']),
           os.path.join("domain",self.domain,self.domain_files['hydrotbl']),
           os.path.join("domain",self.domain,self.domain_files['geogrid']),
           os.path.join("restart",self.storm, self.restart_files['hydro']),
           os.path.join("domain",self.domain,self.domain_files['routelink']),
           os.path.join("domain",self.domain,self.domain_files['lakeparm']),
           os.path.join("domain",self.domain,self.domain_files['gbucketparm']),
           os.path.join("domain",self.domain,self.domain_files['spweight']),
           os.path.join("nudgingTimeSliceObs", self.storm),
           os.path.join("domain",self.domain,self.domain_files['nudgingparm']),
           os.path.join("restart",self.storm, self.restart_files['nudginglastobs']),
           self.duration_hours * 4
          )


        cf = os.path.join(self.comin_nwm,hydro_cfg) 
        with open(cf, 'w+') as f:
            f.write(lines)



    def check_files(self, ini):
        
        msg = "\nFollowing files not found - can not continue"
        mlen = len(msg)

        for f in self.domain_files.keys():
            domain = os.path.join(self.data_path, "domain", self.domain, self.domain_files[f])
            if not os.path.isfile(domain):
               msg += "\n" + self.domain_files[f]


        # 2016100822.LDASIN_DOMAIN1
        forcing = [os.path.join(self.data_path, "forcing", self.storm, f) for f in self.forcing_files]
        for f in forcing:
            if not os.path.isfile(f):
               msg += "\n" + f

    
        slices = [os.path.join(self.data_path, "nudgingTimeSliceObs",self.storm, f) for f in self.discharge_obs_files]
        for f in slices:
            if not os.path.isfile(f):
               msg += "\n" + f


        for f in self.restart_files.keys():
            restart = os.path.join(self.data_path, "restart", self.storm, self.restart_files[f])
            if not os.path.isfile(restart):
               msg += "\n" + self.restart_files[f]

        
        for f in self.config_files.keys():
            if not os.path.isfile(os.path.join(self.data_path,self.config_files[f])):
               msg += "\n" + self.config_files[f]


        tables = [os.path.join(self.data_path,f) for f in self.table_files]
        for f in tables:
            if not os.path.isfile(f):
               msg += "\n" + f


        if len(msg) > mlen:
            print(nus.colory("red", msg))
            sys.exit(0)
        else:
            print(nus.colory("green", "input files exist - good to go"))




    def install_data(self, rundir=None):         
        """ moves or creates link to runtime location of data (i.e. comin)"""
        path_to_dest = self.comin_nwm
        if rundir:
            path_to_dest = rundir

        print("\nInstalling NWM input data in %s" %path_to_dest)

        if rundir:
            if not os.path.exists(path_to_dest):
              try:
                  subprocess.run(['mkdir', '-vp', path_to_dest ], check=True)
              except subprocess.CalledProcessError as err:
                  print('Error in creating %s directory: ' %(path_to_dest, err))             

        path_to_sorc = self.data_path
        
        # for domain data files, if doesn't exist
        to_domain = os.path.join(path_to_dest, "domain")
        fr_domain = os.path.join(path_to_sorc, "domain", self.domain)
        if os.path.islink(os.path.join(path_to_dest,to_domain)):
          print("Link already exists to %s" %to_domain)
        else:
          try:
            print("Creating link to %s" %("domain") )
            subprocess.run(['ln', '-s', fr_domain, "domain"], check=True, cwd=path_to_dest)
          except subprocess.CalledProcessError as err:
            print('Error linking %s: \n' %err)

        # directories to be created for other data, if do not exist
        dirs = ["forcing","restart", "nudgingTimeSliceObs"]
        for d in dirs:
          if os.path.islink(os.path.join(path_to_dest,d)):
            print("Link already exists to %s" %d)
          else:
            try:
              print("Creating link to %s" %(d) )
              subprocess.run(['ln', '-s', os.path.join(path_to_sorc,d,self.storm), d], check=True, cwd=path_to_dest)
            except subprocess.CalledProcessError as err:
              print('Error linking %s: ' %err)
        
        
        for f in self.config_files.keys():
          file = os.path.join(path_to_sorc, self.config_files[f])
          try:
            print("Copying file %s" %(file) )
            subprocess.run(['cp', file, '.' ], check=True, cwd=path_to_dest)
          except subprocess.CalledProcessError as err:
              print('Error copying file %s: ' %err)
        
 
        for f in self.table_files:
          file = os.path.join(path_to_sorc, f)
          try:
            print("Copying file %s" %(file) )
            subprocess.run(['cp', file, '.' ], check=True, cwd=path_to_dest)
          except subprocess.CalledProcessError as err:
            print('Error copying fils %s: ' %err)

        

def prep_all(ini):
    print("\nPreparing data for all models...")



def prep_nwm(ini, start_date_str, duration_hours):
    
    """prepares and moves the data to the runtime location, also creates a
    python module of the same for alternative use with other scripts.  """

    print("\nPreparing data for NWM ...")
   
    # construct NWM input file names
    nwm_obj = NWM(ini, start_date_str, duration_hours)

    # check if all the required files are processed and in place
    nwm_obj.check_files(ini)

    # this method is not used but kept for historical reason.
    # at this time we are preprocessing nwm config files and
    # locate them in nwm data directory and transfer from there!!
    # nwm_obj.check_configs(ini)

    # create links or move the files into run directory
    # Note: I think per nco with one model this should go into com
    # directory!! I put them into both to fix later, if we need to.
    nwm_obj.install_data(ini.RUNdir)

    return nwm_obj
    

def nsem_prep(args=None):

    print("\nPreparing NSEM models data ...")
  
    # below variables are common to all models
    nco, ini = fnw.nsem_workflow(args)     # make sure user has run the workflow and nco structure is in place.
    #sorc_dir = nco.source_dir()

    # import the initialization file
    ini = nus.import_file(args.ini)
   
    # trying to make the functions as independent as 
    # possible without much of performance hit, so
    # not calling previous subprocess, where possible.

    # process start time. all models data are using this time either as part of their file names 
    # or using this time in their configuration files. (i.e. NWM file names are built based on time)
    s_year = ini.model_configure['start_year']
    s_month = ini.model_configure['start_month']
    s_day = ini.model_configure['start_day']
    s_hour = ini.model_configure['start_hour']
    s_min = ini.model_configure['start_minute']
    s_sec = ini.model_configure['start_second']
    tot_hrs = ini.model_configure['nhours_fcst']   # period of data records as well as model runtime per storm
    start_date_str = '{}-{}-{} {}:{}:{}'.format(s_year,s_month,s_day,s_hour,s_min,s_sec)


    if not args.nwm and not args.adc and not args.ww3 and not args.ww3data and not args.atm and not args.atmesh:
        prep_all(ini)

    if args.nwm:
        nwm_obj = prep_nwm(ini, start_date_str, tot_hrs)

    if args.adc:
        prep_nwm(ini)
    if args.ww3:
       prep_nwm(ini)
    if args.ww3data:
       prep_nwm(ini)
    if args.atm:
       prep_nwm(ini)
    if args.atmesh:
       prep_nwm(ini)
    
    # copy nems configs & slurm job and NEMS.x to rundir destinations
    # Note: for now copying into rundir this way. Must be code right.
    print("\nCopying files ...")

    # create links or move the files into run directory
    # because we are not sure about this location yet, using
    # same method to duplicate the same in rundir for now.
    rundir = ini.RUNdir
    sorc_dir = ini.SORCnsem
    repo = ini.repository
    local_repo = os.path.join(sorc_dir, Path(repo).name)
    slurm_job = ini.RUN_TYPE+".job"
    shutil.copy(os.path.join(local_repo,'nems.configure'), rundir)
    shutil.copy(os.path.join(local_repo,'model_configure'), rundir)
    shutil.copy(os.path.join(local_repo,slurm_job), rundir)
    shutil.copy(os.path.join(local_repo,'NEMS/exe/NEMS.x'), rundir)
    print("Finished copying files %s, %s, %s, %s\n" %('nems.configure', 'model_configure', slurm_job, 'NEMS.x'))


