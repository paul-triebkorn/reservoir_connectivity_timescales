#!/bin/bash

# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix

data_dir=/path/to

create_bundle_connectome(){
    tract=$1
    tck2connectome  ${dwi_dir}/TractSeg/tck_segmentations/${tract}.tck \
                    ${dwi_dir}/nodes_${parcellation}.nii.gz \
                    ${dwi_dir}/TractSeg/tck_segmentations/bundle_connectome_${tract}_weights_${parcellation}.txt \
                    -symmetric -zero_diagonal \
                    -tck_weights_in ${dwi_dir}/TractSeg/tck_segmentations/sift2_weights_${tract}.txt \
                    -force -nthreads 1

    tck2connectome  -scale_length -stat_edge mean \
                    ${dwi_dir}/TractSeg/tck_segmentations/${tract}.tck \
                    ${dwi_dir}/nodes_${parcellation}.nii.gz \
                    ${dwi_dir}/TractSeg/tck_segmentations/bundle_connectome_${tract}_lengths_${parcellation}.txt \
                    -symmetric -zero_diagonal \
                    -tck_weights_in ${dwi_dir}/TractSeg/tck_segmentations/sift2_weights_${tract}.txt \
                    -force -nthreads 1

}
export -f create_bundle_connectome

while read sub
do      
        echo $sub
	export dwi_dir=$data_dir/$sub/"T1w"/"Diffusion"
	export tck_dir=$data_dir/$sub/T1w/Diffusion/TractSeg/tck_segmentations
	export parcellation="Schaefer2018_400Parcels_7Networks"
	export bundle_list="/path/to/scripts/TractSeg_tract_list.txt" 
	export nthreads=32
	
	# use the extracted tracts from TractSeg to build a mask on the connectome
        cat $bundle_list | xargs -I % -P $nthreads bash -c 'create_bundle_connectome %'
done < sublist.txt
