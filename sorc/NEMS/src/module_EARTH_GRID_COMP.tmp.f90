















!-----------------------------------------------------------------------
!
      MODULE module_EARTH_GRID_COMP
!
!-----------------------------------------------------------------------
!***  This module contains codes directly related to the EARTH component.
!-----------------------------------------------------------------------
!
!-----------------------------------------------------------------------
!  2010-03-24  Black - Created Earth component module.
!  2010-04     Yang  - Added Ensemble capability.
!  2011-05-11  Theurich & Yang - Modified for using the ESMF 5.2.0r_beta_snapshot_07.
!  2011-10-04  Yang - Modified for using the ESMF 5.2.0r library.
!  2012-02     Tripp - Added ESMF superstructure to support an OCN model
!  2013-06     Theurich - Reworked OCN dependency to be NUOPC based
!  2013-07     Theurich - Macro based ESMF error handling
!-----------------------------------------------------------------------
!
!***  The EARTH component lies in the hierarchy seen here:
!
!          Main program
!               |
!               |
!          NEMS component
!               |     |________________________.
!               |                              |
!          EARTH component        Ensemble Coupler component
!              /|!             / | !          ATM/OCN/ICE/WAV/LND/IPM/HYD .. components
!          |    |   |
!          |    |   (CICE, etc.)
!          |    |
!          |    (MOM5, MOM6, HYCOM, POM, etc.)
!          |
!          CORE component (GSM, NMM, FV3, etc.)
!
!-----------------------------------------------------------------------
!
      USE ESMF

      use NUOPC
      use NUOPC_Driver, &
        Driver_routine_SS             => SetServices, &
        Driver_label_SetModelServices => label_SetModelServices, &
        Driver_label_SetRunSequence   => label_SetRunSequence, &
        Driver_label_SetRunClock      => label_SetRunClock, &
        Driver_label_Finalize         => label_Finalize
      use NUOPC_Connector, only: conSS => SetServices


      USE module_NEMS_UTILS,ONLY: ERR_MSG,MESSAGE_CHECK


  ! - Handle build time ATM options:

  ! - Handle build time OCN options:
      use adc_cap,     only: ADCIRC_SS  => SetServices
      use ATMESH,    only: ATMESH_SS  => SetServices

  ! - Handle build time ICE options:
  ! - Handle build time WAV options:
      use WMESMFMD,        only: WW3_SS  => SetServices
  ! - Handle build time LND options:
  ! - Handle build time IPM options:
  ! - Handle build time HYD options:
      use nwm_nuopc_cap,        only: NWM_SS  => SetServices
  ! - Mediator
      use module_MEDIATOR,        only: MED_SS     => SetServices
      use module_MEDSpaceWeather, only: MEDSW_SS   => SetServices

      USE module_EARTH_INTERNAL_STATE,ONLY: EARTH_INTERNAL_STATE        &
                                           ,WRAP_EARTH_INTERNAL_STATE
!
!      USE module_ATM_GRID_COMP
!
      USE module_NEMS_UTILS,ONLY: ERR_MSG,MESSAGE_CHECK
!
!-----------------------------------------------------------------------
!
      IMPLICIT NONE
!
!-----------------------------------------------------------------------
!
      PRIVATE
!
      PUBLIC :: EARTH_REGISTER
      PUBLIC :: VERBOSE_DIAGNOSTICS
!
!-----------------------------------------------------------------------
!

      LOGICAL, PRIVATE :: flag_verbose_diagnostics = .false.


      CONTAINS

      logical function verbose_diagnostics(set)
        !! Mutator for the verbose diagnostics flag; returns true if
        !! verbose diagnostics should be used, and false otherwise.
        !! If the "set" argument is present, then the flag is set to
        !! the given value.
        logical, optional :: set
        if(present(set)) then
           flag_verbose_diagnostics=set
        endif
        verbose_diagnostics=flag_verbose_diagnostics
      end function verbose_diagnostics

!-----------------------------------------------------------------------
!#######################################################################
!-----------------------------------------------------------------------
!
      SUBROUTINE EARTH_REGISTER(EARTH_GRID_COMP,RC_REG)
!
!-----------------------------------------------------------------------
!
!------------------------
!***  Argument Variables
!------------------------
!
      TYPE(ESMF_GridComp) :: EARTH_GRID_COMP                               !<-- The EARTH component
!
      INTEGER,INTENT(OUT) :: RC_REG                                        !<-- Error return code
!
!---------------------
!***  Local Variables
!---------------------
!
      INTEGER :: RC
      type(ESMF_Config)             :: config
      
      ! for test
      type(ESMF_TimeInterval) :: timeStep
      integer                 :: S
      character(25)           :: cname
      type(ESMF_Clock)        :: clock    
!
!-----------------------------------------------------------------------
!***********************************************************************
!-----------------------------------------------------------------------
!
      RC_REG = ESMF_SUCCESS

      MESSAGE_CHECK="Entered EARTH_REGISTER ....."
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)  
!
!-----------------------------------------------------------------------
!***********************************************************************
!-----------------------------------------------------------------------
!
      ! Derive from NUOPC_Driver
      call NUOPC_CompDerive(EARTH_GRID_COMP, Driver_routine_SS, rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=260, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return

      ! specializations:

      call NUOPC_CompSpecialize(EARTH_GRID_COMP, &
        specLabel=Driver_label_SetModelServices, specRoutine=SetModelServices, &
        rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=267, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      
      call NUOPC_CompSpecialize(EARTH_GRID_COMP, &
        specLabel=Driver_label_SetRunSequence, specRoutine=SetRunSequence, &
        rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=272, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return

      !! Beheen - at this time timeStep=11110
      ! requested Clock object is not present
      !call ESMF_GridCompGet(EARTH_GRID_COMP, name=cname, clock=clock, rc=rc)
      !if (ESMF_STDERRORCHECK(rc)) return  ! bail out
      ! ESMF_ClockGet() Object being used before creation  - Bad Object
      !call ESMF_ClockGet(clock, timeStep=timeStep, rc=rc)
      !call ESMF_TimeIntervalGet(timeStep, s=S, rc=rc)
      !write(MESSAGE_CHECK, *) "timeStep in EARTH_REGISTER is: ", S
      !call ESMF_LogWrite(MESSAGE_CHECK, ESMF_LOGMSG_INFO)

     
      ! The NEMS Earth component is currently the top-level driver and
      ! does not need to coordinate Clocks with its parent.
      call ESMF_MethodRemove(EARTH_GRID_COMP, Driver_label_SetRunClock, rc=RC_REG)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=288, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      call NUOPC_CompSpecialize(EARTH_GRID_COMP, &
        specLabel=Driver_label_SetRunClock, specRoutine=NUOPC_NoOp, rc=RC_REG)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=291, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      
      call NUOPC_CompSpecialize(EARTH_GRID_COMP, &
        specLabel=Driver_label_Finalize, specRoutine=Finalize, &
        rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=296, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      
      ! register an internal initialization method
      call NUOPC_CompSetInternalEntryPoint(EARTH_GRID_COMP, ESMF_METHOD_INITIALIZE, &
        phaseLabelList=(/"IPDv04p2"/), userRoutine=ModifyCplLists, rc=rc)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=301, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return

      write(MESSAGE_CHECK,*) "Create config for member: I "
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)

      ! create, open, and set the config
      config = ESMF_ConfigCreate(rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=308, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      call ESMF_ConfigLoadFile(config, "nems.configure", rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=310, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      call ESMF_GridCompSet(EARTH_GRID_COMP, config=config, rc=RC)
      if (ESMF_LogFoundError(RC, msg="Breaking out of subroutine", line=312, file="module_EARTH_GRID_COMP.F90", rcToReturn=RC_REG)) return
      
      ! Added the following Field Dictionary block to the EARTH component level
      ! in order to prevent different dictionary definitions in the lower
      ! components. Doing this here isn't without problems because it
      ! potentially makes the components (ATM & OCN) depend on this environment,
      ! which lowers their transferability to other coupled systems. However,
      ! extending the Field Dictionary is a temporary solution anyway (see the
      ! TODO: below), so this isn't going to stay for ever this way.
      
      ! Extend the NUOPC Field Dictionary to hold required entries.
      !TODO: In the long run this section will not be needed when we have
      !TODO: absorbed the needed standard names into the default dictionary.
      ! -> 20 fields identified as exports by the GSM component
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "air_density_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="air_density_height_lowest", &
          canonicalUnits="kg m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=333, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_zonal_moment_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_zonal_moment_flx", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=344, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_merid_moment_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_merid_moment_flx", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=355, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_sensi_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sensi_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=366, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_sensi_heat_flx_atm_into_ice")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sensi_heat_flx_atm_into_ice", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=377, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_sensi_heat_flx_atm_into_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sensi_heat_flx_atm_into_ocn", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=388, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_laten_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_laten_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=399, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_laten_heat_flx_atm_into_ice")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_laten_heat_flx_atm_into_ice", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=410, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_laten_heat_flx_atm_into_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_laten_heat_flx_atm_into_ocn", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=421, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_down_lw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_lw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=432, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_down_sw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_sw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=443, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_fprec_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_fprec_rate", &
          canonicalUnits="kg s m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=454, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_prec_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_prec_rate", &
          canonicalUnits="kg s m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=465, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_evap_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_evap_rate", &
          canonicalUnits="kg s m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=476, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_evap_rate_atm_into_ice")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_evap_rate_atm_into_ice", &
          canonicalUnits="kg s m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=487, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_evap_rate_atm_into_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_evap_rate_atm_into_ocn", &
          canonicalUnits="kg s m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=498, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_zonal_moment_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_zonal_moment_flx", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=509, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_merid_moment_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_merid_moment_flx", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=520, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_sensi_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_sensi_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=531, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_laten_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_laten_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=542, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_down_lw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_lw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=553, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_down_sw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_sw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=564, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_temp_height2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_temp_height2m", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=575, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_spec_humid_height2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_spec_humid_height2m", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=586, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_u_wind_height10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_u_wind_height10m", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=597, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_v_wind_height10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_v_wind_height10m", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=608, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_zonal_wind_height10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_zonal_wind_height10m", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=619, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_merid_wind_height10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_merid_wind_height10m", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=630, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      !For MOM6 and WW3 variables to match:
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_partitioned_stokes_drift_1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_partitioned_stokes_drift_1", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=642, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_partitioned_stokes_drift_1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_partitioned_stokes_drift_1", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=654, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_partitioned_stokes_drift_2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_partitioned_stokes_drift_2", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=665, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_partitioned_stokes_drift_2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_partitioned_stokes_drift_2", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=676, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
     if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_partitioned_stokes_drift_3")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_partitioned_stokes_drift_3", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=687, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_partitioned_stokes_drift_3")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_partitioned_stokes_drift_3", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=699, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      ! end of MOM6 and WW3 variables to match
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_temp_height_surface")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_temp_height_surface", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=711, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_pres_height_surface")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_pres_height_surface", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=722, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_surface_height")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_surface_height", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=733, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      ! -> Additional fields identified as needed by MOM5 and others...
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_down_sw_vis_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_sw_vis_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=745, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_down_sw_vis_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_sw_vis_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=756, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_down_sw_ir_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_sw_ir_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=767, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_down_sw_ir_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_down_sw_ir_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=778, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_down_sw_vis_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_sw_vis_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=789, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_down_sw_vis_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_sw_vis_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=800, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_down_sw_ir_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_sw_ir_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=811, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_down_sw_ir_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_down_sw_ir_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=822, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_sw_vis_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_sw_vis_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=833, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_sw_vis_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_sw_vis_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=844, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_sw_ir_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_sw_ir_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=855, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_sw_ir_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_sw_ir_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=866, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_sw_vis_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_sw_vis_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=877, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_sw_vis_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_sw_vis_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=888, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_sw_ir_dir_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_sw_ir_dir_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=899, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_sw_ir_dif_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_sw_ir_dif_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=910, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_salt_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_salt_rate", &
          canonicalUnits="kg psu m-2 s", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=921, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_runoff_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_runoff_rate", &
          canonicalUnits="kg m-2 s", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=932, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_calving_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_calving_rate", &
          canonicalUnits="kg m-2 s", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=943, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_runoff_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_runoff_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=954, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry(  &
        "mean_calving_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_calving_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=965, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ice_fraction")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ice_fraction", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=976, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_sw_pen_to_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sw_pen_to_ocn", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=987, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_up_lw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_up_lw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=998, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mass_of_overlying_sea_ice")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mass_of_overlying_sea_ice", &
          canonicalUnits="kg", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1009, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "s_surf")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="s_surf", &
          canonicalUnits="psu", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1020, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "freezing_melting_potential")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="freezing_melting_potential", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1031, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      ! following two added for export from MOM6
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "accum_heat_frazil")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="accum_heat_frazil", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1043, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_melt_potential")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_melt_potential", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1054, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "u_surf")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="u_surf", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1065, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "v_surf")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="v_surf", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1076, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_lev")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_lev", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1087, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "wind_stress_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wind_stress_zonal", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1098, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "wind_stress_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wind_stress_merid", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1109, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ocn_current_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ocn_current_zonal", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1120, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ocn_current_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ocn_current_merid", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1131, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ocn_current_idir")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ocn_current_idir", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1142, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ocn_current_jdir")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ocn_current_jdir", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1153, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_surface_slope_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_surface_slope_zonal", &
          canonicalUnits="m m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1164, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_surface_slope_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_surface_slope_merid", &
          canonicalUnits="m m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1175, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_surface_slope_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_surface_slope_zonal", &
          canonicalUnits="m m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1186, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_surface_slope_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_surface_slope_merid", &
          canonicalUnits="m m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1197, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_air_ice_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_air_ice_zonal", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1208, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_air_ice_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_air_ice_merid", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1219, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_air_ocn_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_air_ocn_zonal", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1230, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_air_ocn_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_air_ocn_merid", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1241, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_ocn_ice_zonal")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_ocn_ice_zonal", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1252, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_ocn_ice_merid")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_ocn_ice_merid", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1263, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_ocn_ice_idir")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_ocn_ice_idir", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1274, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "stress_on_ocn_ice_jdir")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="stress_on_ocn_ice_jdir", &
          canonicalUnits="N m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1285, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mixed_layer_depth")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mixed_layer_depth", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1296, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_lw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_lw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1307, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_net_sw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_net_sw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1318, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_up_lw_flx_ice")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_up_lw_flx_ice", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1329, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_up_lw_flx_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_up_lw_flx_ocn", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1340, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_lw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_lw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1351, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_net_sw_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_net_sw_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1362, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ir_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ir_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1373, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ir_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ir_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1384, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_vis_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_vis_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1395, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_vis_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_vis_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1406, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ocn_ir_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ocn_ir_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1417, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ocn_ir_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ocn_ir_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1428, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ocn_vis_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ocn_vis_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1439, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ocn_vis_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ocn_vis_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1450, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ice_ir_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ice_ir_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1461, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ice_ir_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ice_ir_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1472, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ice_vis_dir_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ice_vis_dir_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1483, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_ice_vis_dif_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_ice_vis_dif_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1494, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_land_sea_mask")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_land_sea_mask", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1505, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_temp_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_temp_height_lowest", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1516, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_spec_humid_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_spec_humid_height_lowest", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1527, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "humidity_2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="humidity_2m", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1538, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_zonal_wind_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_zonal_wind_height_lowest", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1549, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_merid_wind_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_merid_wind_height_lowest", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1560, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_pres_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_pres_height_lowest", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1571, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "inst_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_height_lowest", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1582, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ocean_mask")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ocean_mask", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1593, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "ice_mask")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="ice_mask", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1604, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "land_mask")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="land_mask", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1615, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      ! special HYCOM exports
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "surface_downward_eastward_stress")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_downward_eastward_stress", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1627, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "surface_downward_northward_stress")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_downward_northward_stress", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1638, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "wind_speed_height10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wind_speed_height10m", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1649, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "wind_speed_squared_10m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wind_speed_squared_10m", &
          canonicalUnits="m2 s-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1660, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "friction_speed")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="friction_speed", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1671, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_lat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_lat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1682, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_sens_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sens_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1693, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "water_flux_into_sea_water")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="water_flux_into_sea_water", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1704, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "frozen_water_flux_into_sea_water")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="frozen_water_flux_into_sea_water", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1715, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif 
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "surface_temperature")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_temperature", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1726, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "air_surface_temperature")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="air_surface_temperature", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1737, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "temperature_2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_2m", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1748, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "upward_sea_ice_basal_available_heat_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="upward_sea_ice_basal_available_heat_flux", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1759, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      ! special HYCOM imports
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_area_fraction")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_area_fraction", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1771, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "downward_x_stress_at_sea_ice_base")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="downward_x_stress_at_sea_ice_base", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1782, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "downward_y_stress_at_sea_ice_base")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="downward_y_stress_at_sea_ice_base", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1793, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "downward_sea_ice_basal_solar_heat_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="downward_sea_ice_basal_solar_heat_flux", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1804, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "upward_sea_ice_basal_heat_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="upward_sea_ice_basal_heat_flux", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1815, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "downward_sea_ice_basal_salt_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="downward_sea_ice_basal_salt_flux", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1826, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "downward_sea_ice_basal_water_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="downward_sea_ice_basal_water_flux", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1837, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_surface_temperature")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_surface_temperature", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1848, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_temperature")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_temperature", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1859, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_thickness")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_thickness", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1870, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_x_velocity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_x_velocity", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1881, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "sea_ice_y_velocity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="sea_ice_y_velocity", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1892, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "net_heat_flx_to_ocn")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="net_heat_flx_to_ocn", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1904, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_fresh_water_to_ocean_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_fresh_water_to_ocean_rate", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1915, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_ice_volume")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_ice_volume", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1926, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "mean_snow_volume")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_snow_volume", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1937, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
     
      !Mass flux of liquid runoff
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "Foxx_rofl")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="Foxx_rofl", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1950, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      !Mass flux of frozen runoff
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "Foxx_rofi")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="Foxx_rofi", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1962, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      !Ocean surface boundary layer depth
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "So_bldepth")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="So_bldepth", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=1974, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
 
      ! Synonyms for HYCOM fields
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"surface_downward_eastward_stress",&
                          "mean_zonal_moment_flx           "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=1984, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"surface_downward_northward_stress",&
                          "mean_merid_moment_flx            "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=1991, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"mean_lat_flx       ",&
                          "mean_laten_heat_flx"/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=1998, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"mean_sens_flx      ",&
                          "mean_sensi_heat_flx"/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=2005, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out

      ! DCR - Fields added for Regional Application
      ! ATM-OCN-ICE-LND-HYD
      ! List of exisitng fields
      ! ice_mask, inst_down_lw_flx, inst_down_sw_flx, inst_height_lowest,
      ! inst_merid_wind_height_lowest, inst_pres_height_lowest,
      ! inst_pres_height_surface, inst_spec_humid_height_lowest,
      ! inst_temp_height_lowest, inst_temp_height_surface,
      ! inst_zonal_wind_height_lowest, mean_down_lw_flx, mean_down_sw_flx,
      ! mean_fprec_rate, mean_laten_heat_flx, mean_net_lw_flx, mean_net_sw_flx,
      ! mean_prec_rate, mean_sensi_heat_flx

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "aerodynamic_roughness_length")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="aerodynamic_roughness_length", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2027, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "canopy_moisture_storage")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="canopy_moisture_storage", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2038, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "carbon_dioxide")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="carbon_dioxide", &
          canonicalUnits="ppmv", & ! Units must be clarified
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2049, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "cosine_zenith_angle")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="cosine_zenith_angle", &
          canonicalUnits="degree", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2060, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "exchange_coefficient_heat")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="exchange_coefficient_heat", &
          canonicalUnits="W m-2 K-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2071, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "exchange_coefficient_heat_height2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="exchange_coefficient_heat_height2m", &
          canonicalUnits="W m-2 K-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2082, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "exchange_coefficient_moisture_height2m")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="exchange_coefficient_moisture_height2m", &
          canonicalUnits="kg m-2 s-1 Pa-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2093, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_wind_speed_height_lowest")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_wind_speed_height_lowest", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2104, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_cprec_rate")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_cprec_rate", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2115, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_grnd_sensi_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_grnd_sensi_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2126, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_laten_heat_flx_kinematic")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_laten_heat_flx_kinematic", &
          canonicalUnits="Kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2137, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_surface_albedo")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_surface_albedo", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2148, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_surface_skin_temp")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_surface_skin_temp", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2159, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mixing_ratio_surface")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mixing_ratio_surface", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2170, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "root_moisture")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="root_moisture", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2181, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "saturated_mixing_ratio")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="saturated_mixing_ratio", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2192, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_snow_area_fraction")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_snow_area_fraction", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2203, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_snow_thickness")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_snow_thickness", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2214, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_snow_melt_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_snow_melt_flux", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2225, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_surface_snow")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_surface_snow", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2236, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_depth")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_depth", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2247, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_hydraulic_conductivity_at_saturation")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_hydraulic_conductivity_at_saturation", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2258, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "moisture_content_of_soil_layer")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="moisture_content_of_soil_layer", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2269, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "moisture_content_of_soil_layer_1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="moisture_content_of_soil_layer_1", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2280, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "moisture_content_of_soil_layer_2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="moisture_content_of_soil_layer_2", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2291, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "moisture_content_of_soil_layer_3")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="moisture_content_of_soil_layer_3", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2302, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "moisture_content_of_soil_layer_4")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="moisture_content_of_soil_layer_4", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2313, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_porosity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_porosity", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2324, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temperature_of_soil_layer")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_of_soil_layer", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2335, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temperature_of_soil_layer_1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_of_soil_layer_1", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2346, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temperature_of_soil_layer_2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_of_soil_layer_2", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2357, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temperature_of_soil_layer_3")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_of_soil_layer_3", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2368, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temperature_of_soil_layer_4")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temperature_of_soil_layer_4", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2379, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_temperature_bottom")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_temperature_bottom", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2390, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_type")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_type", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2401, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "soil_moisture_content")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="soil_moisture_content", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2412, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "subsurface_basin_mask")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="subsurface_basin_mask", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2423, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "subsurface_runoff_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="subsurface_runoff_flux", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2434, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_microwave_emissivity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_microwave_emissivity", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2445, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_runoff_flux")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_runoff_flux", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2456, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "vegetation_type")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="vegetation_type", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2467, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "volume_fraction_of_frozen_water_in_soil")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="volume_fraction_of_frozen_water_in_soil", &
          canonicalUnits="m3 m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2478, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_soil_layer")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_soil_layer", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2489, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_soil_layer_1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_soil_layer_1", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2500, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_soil_layer_2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_soil_layer_2", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2511, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_soil_layer_3")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_soil_layer_3", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2522, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "liquid_water_content_of_soil_layer_4")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="liquid_water_content_of_soil_layer_4", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2533, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "volume_fraction_of_total_water_in_soil")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="volume_fraction_of_total_water_in_soil", &
          canonicalUnits="m3 m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2544, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "volume_fraction_of_total_water_in_soil_at_critical_point")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="volume_fraction_of_total_water_in_soil_at_critical_point", &
          canonicalUnits="m3 m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2555, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "volume_fraction_of_total_water_in_soil_at_field_capacity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="volume_fraction_of_total_water_in_soil_at_field_capacity", &
          canonicalUnits="m3 m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2566, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "volume_fraction_of_total_water_in_soil_at_wilting_point")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="volume_fraction_of_total_water_in_soil_at_wilting_point", &
          canonicalUnits="m3 m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2577, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "water_surface_height_above_reference_datum")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="water_surface_height_above_reference_datum", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2588, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_sensi_heat_flx_atm_into_lnd")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_sensi_heat_flx_atm_into_lnd", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2600, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "mean_laten_heat_flx_atm_into_lnd")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="mean_laten_heat_flx_atm_into_lnd", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2612, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      ! Fields from and to WW3

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_wind_at_10m_height")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_wind_at_10m_height", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2626, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"eastward_wind_at_10m_height",&
                          "inst_zonal_wind_height10m  "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=2634, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_wind_at_10m_height")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_wind_at_10m_height", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2645, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"northward_wind_at_10m_height",&
                          "inst_merid_wind_height10m   "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=2653, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out

      !For MOM6 and WW3 variables to match: 
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"surface_eastward_sea_water_velocity",&
                          "ocn_current_zonal                  "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=2662, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      call NUOPC_FieldDictionarySetSyno( &
        standardNames = (/"surface_northward_sea_water_velocity",&
                          "ocn_current_merid                   "/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=2669, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_stokes_drift_current")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_stokes_drift_current", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2680, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_stokes_drift_current")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_stokes_drift_current", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2692, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_wave_bottom_current")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_wave_bottom_current", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2704, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_wave_bottom_current")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_wave_bottom_current", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2716, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "wave_bottom_current_radian_frequency")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wave_bottom_current_radian_frequency", &
          canonicalUnits="rad s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2728, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_wave_radiation_stress_gradient")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_wave_radiation_stress_gradient", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2740, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_wave_radiation_stress_gradient")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_wave_radiation_stress_gradient", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2752, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_wave_radiation_stress")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_wave_radiation_stress", &
          canonicalUnits="N m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2764, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_northward_wave_radiation_stress")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_northward_wave_radiation_stress", &
          canonicalUnits="N m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2776, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_wave_radiation_stress")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_wave_radiation_stress", &
          canonicalUnits="N m-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2788, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "wave_induced_charnock_parameter")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wave_induced_charnock_parameter", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2800, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "wave_z0_roughness_length")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wave_z0_roughness_length", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2812, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "wave_bottom_current_period")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="wave_bottom_current_period", &
          canonicalUnits="s", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2824, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif


      ! Fields from WAM to IPE

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "northward_wind_neutral")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="northward_wind_neutral", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2839, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "eastward_wind_neutral")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="eastward_wind_neutral", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2851, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "upward_wind_neutral")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="upward_wind_neutral", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2863, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "temp_neutral")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="temp_neutral", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2875, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "O_Density")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="O_Density", &
          canonicalUnits="m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2887, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "O2_Density")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="O2_Density", &
          canonicalUnits="m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2899, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "N2_Density")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="N2_Density", &
          canonicalUnits="m-3", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2911, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "height")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="height", &
          canonicalUnits="km", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2923, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      ! Chemistry fields

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_pres_interface")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_pres_interface", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2937, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_pres_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_pres_levels", &
          canonicalUnits="Pa", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2949, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_geop_interface")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_geop_interface", &
          canonicalUnits="m2 s-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2961, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_geop_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_geop_levels", &
          canonicalUnits="m2 s-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2973, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_temp_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_temp_levels", &
          canonicalUnits="K", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2985, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_zonal_wind_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_zonal_wind_levels", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=2997, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_merid_wind_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_merid_wind_levels", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3009, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_omega_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_omega_levels", &
          canonicalUnits="Pa s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3021, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_tracer_mass_frac")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_tracer_mass_frac", &
          canonicalUnits="kg kg-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3033, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_tracer_up_surface_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_tracer_up_surface_flx", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3045, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_tracer_down_surface_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_tracer_down_surface_flx", &
          canonicalUnits="kg m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3057, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_tracer_clmn_mass_dens")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_tracer_clmn_mass_dens", &
          canonicalUnits="g m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3069, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_tracer_anth_biom_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_tracer_anth_biom_flx", &
          canonicalUnits="ug m-2 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3081, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_pbl_height")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_pbl_height", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3093, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "surface_cell_area")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="surface_cell_area", &
          canonicalUnits="m2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3105, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_convective_rainfall_amount")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_convective_rainfall_amount", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3117, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_exchange_coefficient_heat_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_exchange_coefficient_heat_levels", &
          canonicalUnits="W m-2 K-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3129, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_spec_humid_conv_tendency_levels")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_spec_humid_conv_tendency_levels", &
          canonicalUnits="kg kg-1 s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3141, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_friction_velocity")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_friction_velocity", &
          canonicalUnits="m s-1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3153, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_rainfall_amount")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_rainfall_amount", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3165, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_soil_moisture_content")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_soil_moisture_content", &
          canonicalUnits="kg m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3177, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_up_sensi_heat_flx")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_up_sensi_heat_flx", &
          canonicalUnits="W m-2", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3189, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_lwe_snow_thickness")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_lwe_snow_thickness", &
          canonicalUnits="m", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3201, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_vegetation_area_frac")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_vegetation_area_frac", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3213, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      if (.not.NUOPC_FieldDictionaryHasEntry( &
        "inst_surface_roughness")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="inst_surface_roughness", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3225, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

      ! Dummy fields

      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "dummyfield")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="dummyfield", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3239, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "dummyfield1")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="dummyfield1", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3250, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif
      if (.not. NUOPC_FieldDictionaryHasEntry( &
        "dummyfield2")) then
        call NUOPC_FieldDictionaryAddEntry( &
          standardName="dummyfield2", &
          canonicalUnits="1", &
          rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3261, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
      endif

!-----------------------------------------------------------------------
!
      MESSAGE_CHECK="Exited EARTH_REGISTER ....."
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)  

      END SUBROUTINE EARTH_REGISTER
!
!-----------------------------------------------------------------------
!#######################################################################
!-----------------------------------------------------------------------
!

      subroutine SetModelServices(driver, rc)
        type(ESMF_GridComp)  :: driver
        integer, intent(out) :: rc

        ! local variables
        integer                         :: localrc, stat, i, j, petCount
        character(ESMF_MAXSTR)          :: name
        type(WRAP_EARTH_INTERNAL_STATE) :: is
        type(ESMF_GridComp)             :: comp
        type(ESMF_Config)               :: config
        character(len=32), allocatable  :: compLabels(:)
        integer, allocatable            :: petList(:)
        character(len=10)               :: value
        character(len=20)               :: model, prefix
        character(len=160)              :: msg
        integer                         :: petListBounds(2)
        integer                         :: componentCount
        type(NUOPC_FreeFormat)          :: attrFF, fdFF

        rc = ESMF_SUCCESS

        MESSAGE_CHECK="Entered SetModelServices ....."
       CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)


        ! query the Component for info
        call ESMF_GridCompGet(driver, name=name, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3306, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

        ! allocate memory for the internal state and store in Component
        allocate(is%EARTH_INT_STATE, stat=stat)
        if (ESMF_LogFoundAllocError(statusToCheck=stat, &
          msg="Allocation of internal state memory failed.", &
          line=3312, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90", rcToReturn=rc)) &
          return  ! bail out
        call ESMF_GridCompSetInternalState(driver, is, rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3316, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
        
        ! get petCount and config
        call ESMF_GridCompGet(driver, petCount=petCount, config=config, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3321, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
      
        ! read and ingest free format driver attributes
        attrFF = NUOPC_FreeFormatCreate(config, label="EARTH_attributes::", &
          relaxedflag=.true., rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3327, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

        call NUOPC_CompAttributeIngest(driver, attrFF, addFlag=.true., rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3331, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

        call NUOPC_FreeFormatDestroy(attrFF, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3335, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
        
        ! dump the current field dictionary into the Log file
        call ESMF_AttributeGet(driver, name="DumpFieldDictionary", &
          value=value, defaultValue="false", &
          convention="NUOPC", purpose="Instance", rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3342, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

        if (trim(value)=="true") then
          call ESMF_LogWrite( &
            "===>===>===>===> Begin Dumping Field Dictionary <===<===<===<===",&
            ESMF_LOGMSG_INFO, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3349, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          call NUOPC_FieldDictionaryEgest(fdFF, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3352, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          call NUOPC_FreeFormatLog(fdFF, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3355, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          call ESMF_LogWrite( &
            "===>===>===>===> Done Dumping Field Dictionary <===<===<===<===", &
            ESMF_LOGMSG_INFO, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3360, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
        endif
        
        ! determine the generic component labels
        componentCount = ESMF_ConfigGetLen(config, &
          label="EARTH_component_list:", rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3367, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
        allocate(compLabels(componentCount), stat=stat)
        if (ESMF_LogFoundAllocError(statusToCheck=stat, &
          msg="Allocation of compLabels failed.", &
          line=3371, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90", rcToReturn=rc)) &
          return  ! bail out
        call ESMF_ConfigGetAttribute(config, valueList=compLabels, &
          label="EARTH_component_list:", count=componentCount, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=3376, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
        
        ! determine information for each component and add to the driver
        do i=1, componentCount
          ! construct component prefix
          prefix=trim(compLabels(i))
      
          ! read in petList bounds
          call ESMF_ConfigGetAttribute(config, petListBounds, &
            label=trim(prefix)//"_petlist_bounds:", default=-1, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3387, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

          ! handle the default situation
          if (petListBounds(1)==-1 .or. petListBounds(2)==-1) then
            petListBounds(1) = 0
            petListBounds(2) = petCount - 1
          endif

          ! read in model instance name
          call ESMF_ConfigGetAttribute(config, model, &
            label=trim(prefix)//"_model:", default="none", rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3399, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          ! check that there was a model instance specified
          if (trim(model) == "none") then
            ! Error condition: no model was specified
            write (msg, *) "No model was specified for component: ",trim(prefix)
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3404, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          endif
          ! set petList for this component
          allocate(petList(petListBounds(2)-petListBounds(1)+1))
          do j=petListBounds(1), petListBounds(2)
            petList(j-petListBounds(1)+1) = j ! PETs are 0 based
          enddo
          
          if (trim(model) == "satm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3423, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xatm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3436, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "datawam") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3449, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "gsm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3462, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "nmmb") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3475, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "fv3") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3488, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "datm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3501, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "socn") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3514, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xocn") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3527, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "hycom") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3540, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "mom5") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3553, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "mom6") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3566, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "pom") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3579, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "sice") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3592, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xice") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3605, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "cice") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3618, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "swav") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3631, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xwav") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3644, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "ww3") then
            call NUOPC_DriverAddComp(driver, trim(prefix), WW3_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
              line=3653, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          elseif (trim(model) == "slnd") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3670, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xlnd") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3683, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "noah") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3696, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "lis") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3709, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "sipm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3722, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xipm") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3735, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "ipe") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3748, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "dataipe") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3761, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "shyd") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3774, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "xhyd") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3787, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "wrfhydro") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3800, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "gsdchem") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3813, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "adcirc") then
            call NUOPC_DriverAddComp(driver, trim(prefix), ADCIRC_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
              line=3822, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  !  bail out
          elseif (trim(model) == "hwrfdata") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3839, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "ww3data") then
            write (msg, *) "Model '", trim(model), "' was requested, "// &
              "but is not available in the executable!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3852, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          elseif (trim(model) == "atmesh") then
            call NUOPC_DriverAddComp(driver, trim(prefix), ATMESH_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
              line=3861, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  !  bail out
          elseif (trim(model) == "nwm") then
            call NUOPC_DriverAddComp(driver, trim(prefix), NWM_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
              line=3874, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  !  bail out
! - Two mediator choices currently built into NEMS from internal
          elseif (trim(model) == "nems") then
            call NUOPC_DriverAddComp(driver, trim(prefix), MED_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
              line=3887, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          elseif (trim(model) == "spaceweather") then
            call NUOPC_DriverAddComp(driver, trim(prefix), MEDSW_SS, &
              petList=petList, comp=comp, rc=rc)
            if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
             line=3892, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          else
            ! Error condition: unknown model requested
            write (msg, *) "The requested model '", trim(model), &
              "' is an invalid choice!"
            call ESMF_LogSetError(ESMF_RC_NOT_VALID, msg=msg, line=3897, &
              file="module_EARTH_GRID_COMP.F90", rcToReturn=rc)
            return  ! bail out
          endif
          
          ! read and ingest free format component attributes
          attrFF = NUOPC_FreeFormatCreate(config, &
            label=trim(prefix)//"_attributes::", relaxedflag=.true., rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3906, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          call NUOPC_CompAttributeIngest(comp, attrFF, addFlag=.true., rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3909, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          call NUOPC_FreeFormatDestroy(attrFF, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3912, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
          
          ! clean-up
          deallocate(petList)
          
        enddo
        

        ! clean-up
        deallocate(compLabels)

      MESSAGE_CHECK="Exited SetModelServices ....."
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)  
      end subroutine

  !-----------------------------------------------------------------------------
  
  subroutine SetRunSequence(driver, rc)
    type(ESMF_GridComp)  :: driver
    integer, intent(out) :: rc
    
    ! local variables
    character(ESMF_MAXSTR)          :: name
    type(ESMF_Config)               :: config
    type(NUOPC_FreeFormat)          :: runSeqFF

    rc = ESMF_SUCCESS

      MESSAGE_CHECK="Entered SetRunSequence ....."
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)  

    ! query the Component for info
    call ESMF_GridCompGet(driver, name=name, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=3955, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

    ! read free format run sequence from config
    call ESMF_GridCompGet(driver, config=config, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=3961, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
    runSeqFF = NUOPC_FreeFormatCreate(config, label="runSeq::", rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=3964, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out

    ! ingest FreeFormat run sequence
    call NUOPC_DriverIngestRunSequence(driver, runSeqFF, &
      autoAddConnectors=.true., rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=3970, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
    
    ! Diagnostic output
    if(verbose_diagnostics()) then
       call NUOPC_DriverPrint(driver, orderflag=.true., rc=rc)
       if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=3982, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
    endif
    
      MESSAGE_CHECK="Exited SetRunSequence ....."
      CALL ESMF_LogWrite(MESSAGE_CHECK,ESMF_LOGMSG_INFO,rc=RC)  
  end subroutine
    
  !-----------------------------------------------------------------------------

  !-----------------------------------------------------------------------------

  subroutine Finalize(driver, rc)
    type(ESMF_GridComp)  :: driver
    integer, intent(out) :: rc
    
    ! local variables
    integer                         :: localrc, stat
    type(WRAP_EARTH_INTERNAL_STATE) :: is
    logical                         :: existflag
    character(ESMF_MAXSTR)          :: name

    rc = ESMF_SUCCESS

    ! query the Component for info
    call ESMF_GridCompGet(driver, name=name, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4288, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
    
    ! query Component for this internal State
    nullify(is%EARTH_INT_STATE)
    call ESMF_GridCompGetInternalState(driver, is, rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4294, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90")) return  ! bail out
      
    ! deallocate internal state memory
    deallocate(is%EARTH_INT_STATE, stat=stat)
    if (ESMF_LogFoundDeallocError(statusToCheck=stat, &
      msg="Deallocation of internal state memory failed.", &
      line=4300, file=trim(name)//":"//"module_EARTH_GRID_COMP.F90", rcToReturn=rc)) &
      return  ! bail out
      
  end subroutine
      
  !-----------------------------------------------------------------------------
  
  recursive subroutine ModifyCplLists(driver, importState, exportState, clock, &
    rc)
    type(ESMF_GridComp)  :: driver
    type(ESMF_State)     :: importState, exportState
    type(ESMF_Clock)     :: clock
    integer, intent(out) :: rc

    character(len=160)              :: name, msg
    type(ESMF_CplComp), pointer     :: connectorList(:)
    integer                         :: i, j, cplListSize
    character(len=160), allocatable :: cplList(:)
    character(len=160)              :: value
    type(WRAP_EARTH_INTERNAL_STATE) :: is

    rc = ESMF_SUCCESS
    
    ! query Component for this internal State
    nullify(is%EARTH_INT_STATE)
    call ESMF_GridCompGetInternalState(driver, is, rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4327, &
      file="module_EARTH_GRID_COMP.F90")) &
      return  ! bail out

    call ESMF_LogWrite("Driver is in ModifyCplLists()", ESMF_LOGMSG_INFO, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4333, &
      file="module_EARTH_GRID_COMP.F90")) &
      return  ! bail out
    
    nullify(connectorList)
    call NUOPC_DriverGetComp(driver, compList=connectorList, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4340, &
      file="module_EARTH_GRID_COMP.F90")) &
      return  ! bail out
    
    write (msg,*) "Found ", size(connectorList), " Connectors."// &
      " Modifying CplList Attribute...."
    call ESMF_LogWrite(trim(msg), ESMF_LOGMSG_INFO, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=4348, &
      file="module_EARTH_GRID_COMP.F90")) &
      return  ! bail out
      
    do i=1, size(connectorList)
      ! query Connector i for its name
      call ESMF_CplCompGet(connectorList(i), name=name, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=4356, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      ! access CplList for Connector i
      call NUOPC_CompAttributeGet(connectorList(i), name="CplList", &
        itemCount=cplListSize, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=4363, &
        file="module_EARTH_GRID_COMP.F90")) &
        return  ! bail out
      if (cplListSize>0) then
        allocate(cplList(cplListSize))
        call NUOPC_CompAttributeGet(connectorList(i), name="CplList", &
          valueList=cplList, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=4371, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
        ! go through all of the entries in the cplList and add options
        do j=1, cplListSize
          cplList(j) = trim(cplList(j))//":DumpWeights=true"
          cplList(j) = trim(cplList(j))//":SrcTermProcessing=1:TermOrder=SrcSeq"
          ! add connection options read in from configuration file
          call ESMF_AttributeGet(connectorList(i), name="ConnectionOptions", &
            value=value, defaultValue="", rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=4382, &
            file="module_EARTH_GRID_COMP.F90")) &
            return  ! bail out
          cplList(j) = trim(cplList(j))//trim(value)
        enddo
        ! store the modified cplList in CplList attribute of connector i
        call NUOPC_CompAttributeSet(connectorList(i), &
          name="CplList", valueList=cplList, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=4391, &
          file="module_EARTH_GRID_COMP.F90")) &
          return  ! bail out
        deallocate(cplList)
      endif
    enddo
      
    deallocate(connectorList)
    
  end subroutine

  !-----------------------------------------------------------------------------
!
!-----------------------------------------------------------------------
!
      END MODULE module_EARTH_GRID_COMP
!
!-----------------------------------------------------------------------
