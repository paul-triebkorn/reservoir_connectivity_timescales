#!/bin/bash
# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix


results_dir="/path/to/"
nthreads=30
export OMP_NUM_THREADS=$nthreads
ntracks=15M
scripts_dir="/path/to/scripts/"

while read sub
do 
   echo $sub
   dwi_dir=${results_dir}/${sub}/T1w/Diffusion
   dwi_log=${dwi_dir}/${sub}_out.txt
   if [ ! -f  ${dwi_dir}/response_wm.txt ]
   then
      echo "Preprocessing files are missing."
      continue
   fi


   # create mask
   dwi2mask ${dwi_dir}/data.nii.gz ${dwi_dir}/mask.mif.gz \
       -fslgrad ${dwi_dir}/bvecs ${dwi_dir}/bvals \
       -force -nthreads $nthreads >> $dwi_log 2>&1

   # create fod images
   dwi2fod msmt_csd ${dwi_dir}/data.nii.gz \
		    ${scripts_dir}/avg_response_wm.txt  ${dwi_dir}/wm_fod.mif.gz \
                    ${scripts_dir}/avg_response_gm.txt  ${dwi_dir}/gm_fod.mif.gz \
                    ${scripts_dir}/avg_response_csf.txt ${dwi_dir}/csf_fod.mif.gz \
                    -fslgrad ${dwi_dir}/bvecs ${dwi_dir}/bvals \
                    -mask ${dwi_dir}/mask.mif.gz -force -nthreads $nthreads >> $dwi_log 2>&1

   # normalise fods
   mtnormalise  ${dwi_dir}/wm_fod.mif.gz  ${dwi_dir}/wm_fod_norm.mif.gz \
                ${dwi_dir}/gm_fod.mif.gz  ${dwi_dir}/gm_fod_norm.mif.gz \
                ${dwi_dir}/csf_fod.mif.gz ${dwi_dir}/csf_fod_norm.mif.gz \
                -mask ${dwi_dir}/mask.mif.gz -force -nthreads $nthreads >> $dwi_log 2>&1

   # Create 5TT image for ACT
   5ttgen freesurfer $results_dir/$sub/T1w/aparc+aseg.nii.gz ${dwi_dir}/5tt.mif.gz -force >> $dwi_log 2>&1

   # generate streamlines
   tckgen ${dwi_dir}/wm_fod_norm.mif.gz ${dwi_dir}/${ntracks}.tck -algorithm iFOD2 \
         -act ${dwi_dir}/5tt.mif.gz \
         -seed_dynamic ${dwi_dir}/wm_fod_norm.mif.gz \
         -maxlength 250 \
         -backtrack \
         -select ${ntracks} -force -nthreads ${nthreads} >> $dwi_log 2>&1

   # perform tract filtering using the SIFT2 algorithm
   tcksift2 -act ${dwi_dir}/5tt.mif.gz \
               ${dwi_dir}/${ntracks}.tck \
               ${dwi_dir}/wm_fod_norm.mif.gz ${dwi_dir}/sift2_weights_${ntracks}.txt \
               -force -nthreads ${nthreads} >> $dwi_log 2>&1

done < sublist.txt


