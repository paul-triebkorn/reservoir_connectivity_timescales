#!/bin/bash
# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix


nthreads=32
data_dir=/path/to

while read sub
do  
    dwi_dir=$data_dir/$sub/T1w/Diffusion/
    dwi_log=$dwi_dir/${sub}_out.txt
    dwi2response dhollander $dwi_dir/data.nii.gz \
            -fslgrad $dwi_dir/bvecs $dwi_dir/bvals \
            $dwi_dir/response_wm.txt \
            $dwi_dir/response_gm.txt \
            $dwi_dir/response_csf.txt \
            -voxels ${dwi_dir}/response_voxels.mif.gz \
            -nthreads ${nthreads} -force >> $dwi_log 2>&1

done < sublist.txt
