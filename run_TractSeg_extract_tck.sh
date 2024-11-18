#!/bin/bash
nthreads=35
export OMP_NUM_THREADS=$nthreads

# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix

extract_tck(){
	tract=$1
	echo "Processing tract : ${tract}"
	# create exclusion mask
	mrcalc $bundle_dir/${tract}.nii.gz \
		   $endings_dir/${tract}_e.nii.gz -add \
		   $endings_dir/${tract}_b.nii.gz -add \
		   $exclusion_dir/${tract}.nii.gz -force 

	mrthreshold $exclusion_dir/${tract}.nii.gz -invert \
			    $exclusion_dir/${tract}.nii.gz -force

	# filter tractogram
	tckedit $full_tck_file $tck_dir/${tract}.tck \
			-tck_weights_in $dwi_dir/sift2_weights_${ntracts}.txt \
			-tck_weights_out $tck_dir/sift2_weights_${tract}.txt \
			-exclude $exclusion_dir/${tract}.nii.gz  \
			-include $endings_dir/${tract}_b.nii.gz \
			-include $bundle_dir/${tract}.nii.gz \
			-include $endings_dir/${tract}_e.nii.gz \
			-nthreads 1 -force
}
export -f extract_tck

while read sub
do
	export dwi_dir=/path/to/${sub}/T1w/Diffusion
	export ntracts=15M
	export full_tck_file=$dwi_dir/${ntracts}.tck
	export tract_seg_dir=$dwi_dir/TractSeg/
	export endings_dir=$tract_seg_dir/endings_segmentations
	export bundle_dir=$tract_seg_dir/bundle_segmentations
	export exclusion_dir=$tract_seg_dir/exclusion_segmentations
	if [ ! -d $exclusion_dir ]; then
		mkdir $exclusion_dir   
	fi
	
	export tck_dir=$tract_seg_dir/tck_segmentations
	if [ ! -d $tck_dir ]; then
		mkdir $tck_dir    
	fi

	# process tracts in parallel
	cat TractSeg_tract_list.txt | xargs -I % -P $nthreads bash -c 'extract_tck %'
done < sublist.txt
