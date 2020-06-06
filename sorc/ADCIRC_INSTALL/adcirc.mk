# ESMF self-describing build dependency makefile fragment

ESMF_DEP_FRONT     = adc_cap
ESMF_DEP_INCPATH   = /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC/cpl/nuopc /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC_INSTALL 
ESMF_DEP_CMPL_OBJS = 
ESMF_DEP_LINK_OBJS =  -L/scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC_INSTALL -ladc /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC_INSTALL/libadc_cap.a  -L/scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC/work/  /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/ADCIRC/work/libadc.a  
