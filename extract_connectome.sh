#!/bin/bash
# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix


export n_parcels=500
export n_nets=7
export results_dir=/path/to
export parcellation=Schaefer2018_${n_parcels}Parcels_${n_nets}Networks
export parc_lut=/path/to/scripts/Schaefer_parc/Parcellations/project_to_individual/Schaefer2018_${n_parcels}Parcels_${n_nets}Networks_order_LUT.txt
export mrtrix_lut=/path/to/scripts/Schaefer_mrtrix_lut/Schaefer2018_${n_parcels}Parcels_${n_nets}Networks_order_LUT.txt
export ntracks=15M
export nthreads=1

# while read sub
# do
extract_connectome(){
    sub=$1
    dwi_dir=${results_dir}/${sub}/T1w/Diffusion
    T1w_dir=${results_dir}/${sub}/T1w/
    
    
    if [ ! -f ${dwi_dir}/${ntracks}.tck ]; 
    then
        echo "${dwi_dir}/${ntracks}.tck is not available."
        exit
    fi
    
    # bring parcellation image into dwi space
    labelconvert ${T1w_dir}/${parcellation}.nii.gz \
                    ${parc_lut} \
                    ${mrtrix_lut} \
                    ${dwi_dir}/nodes_${parcellation}.nii.gz -nthreads ${nthreads} -force 
    
    # create connectome weights and length matrix
    tck2connectome  ${dwi_dir}/${ntracks}.tck \
                    ${dwi_dir}/nodes_${parcellation}.nii.gz \
                    ${dwi_dir}/weights_${parcellation}_${ntracks}.txt -symmetric -zero_diagonal \
                    -tck_weights_in ${dwi_dir}/sift2_weights_${ntracks}.txt \
                    -out_assignments ${dwi_dir}/assignment_${parcellation}_${ntracks}.txt \
                    -force -nthreads ${nthreads} 

    tck2connectome  -scale_length -stat_edge mean \
                    ${dwi_dir}/${ntracks}.tck \
                    ${dwi_dir}/nodes_${parcellation}.nii.gz \
                    ${dwi_dir}/lengths_${parcellation}_${ntracks}.txt -symmetric -zero_diagonal \
                    -tck_weights_in ${dwi_dir}/sift2_weights_${ntracks}.txt \
                    -force -nthreads ${nthreads} 
}
# done < sublist.txt
export -f extract_connectome

cat sublist.txt | xargs -I % -P 35 bash -c 'extract_connectome %'

