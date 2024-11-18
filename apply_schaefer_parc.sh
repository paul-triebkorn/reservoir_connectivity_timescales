#!/bin/bash

# Freesurfer: set environment variables
# use Freesurfer v7
export FREESURFER_HOME=/path/to/freesurfer_v7.4.0
export SUBJECTS_DIR=$FREESURFER_HOME/subjects
source $FREESURFER_HOME/SetUpFreeSurfer.sh
which mri_aparc2aseg

export StudyFolder=/path/to/
export Schaefer_parc_dir=/path/to/scripts/Schaefer_parc/gcs
nthreads=50

apply_parc(){
  Subject=$1
  export SUBJECTS_DIR=$StudyFolder/$Subject/T1w/

  # project parcellation on cortical surfaces
  for hemi in rh lh
  do
    mris_ca_label -l $SUBJECTS_DIR/$Subject/label/$hemi.cortex.label \
        $Subject $hemi $SUBJECTS_DIR/$Subject/surf/$hemi.sphere.reg \
        $Schaefer_parc_dir/$hemi.Schaefer2018_400Parcels_7Networks.gcs \
        $SUBJECTS_DIR/$Subject/label/$hemi.Schaefer2018_400Parcels_7Networks_order.annot
  done

  # project from cortex into volume
  mri_aparc2aseg --s $Subject \
                --o $SUBJECTS_DIR/$Subject/mri/Schaefer2018_400Parcels_7Networks.mgz \
                --annot Schaefer2018_400Parcels_7Networks_order

  # apply same steps as in HCP pipeline /PostFreeSurfer/scripts/FreeSurfer2CaretConvertAndRegisterNonlinear.sh
  # to map parcellations from freesurfer 1mm res to highres 0.7mm
  T1wFolder=$SUBJECTS_DIR
  T1wImage=T1w_acpc_dc_restore
  FreeSurferFolder=$SUBJECTS_DIR/$Subject
  Image=Schaefer2018_400Parcels_7Networks
  AtlasSpaceFolder="$StudyFolder"/"$Subject"/"MNINonLinear"
  AtlasSpaceT1wImage=T1w_restore
  FreeSurferLabels=/path/to/scripts/Schaefer_parc/Parcellations/project_to_individual/Schaefer2018_400Parcels_7Networks_order_LUT.txt

  mri_convert -rt nearest -rl "$T1wFolder"/"$T1wImage".nii.gz "$FreeSurferFolder"/mri/"$Image".mgz "$T1wFolder"/"$Image"_1mm.nii.gz
  applywarp --rel --interp=nn -i "$T1wFolder"/"$Image"_1mm.nii.gz -r "$AtlasSpaceFolder"/"$AtlasSpaceT1wImage" --premat=$FSLDIR/etc/flirtsch/ident.mat -o "$T1wFolder"/"$Image".nii.gz
}
export -f apply_parc

cat sublist.txt | xargs -I % -P $nthreads bash -c 'apply_parc %'
