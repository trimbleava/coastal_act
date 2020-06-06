#-----------------------------------------------
# NUOPC/ESMF self-describing build dependency
# makefile fragment for Wavewatch III
#-----------------------------------------------
# component module name
ESMF_DEP_FRONT := WMESMFMD
# component module path
ESMF_DEP_INCPATH := /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/WW3/model/mod_HYB
# component module objects
ESMF_DEP_CMPL_OBJS := /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/WW3/model/obj_HYB/libww3_multi_esmf.a(wmesmfmd.o)
# component object/archive list
ESMF_DEP_LINK_OBJS := /scratch2/COASTAL/coastal/save/NAMED_STORMS/COASTAL_ACT/sorc/WW3/model/obj_HYB/libww3_multi_esmf.a 
