#!/bin/bash
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_tractseg

nthreads=35
while read sub
do
	dwi_dir="/path/to/$sub/T1w/Diffusion"
	out_dir=$dwi_dir/"TractSeg"
	
	if [ ! -d $out_dir]; then
		mkdir $out_dir
	fi
	
	# TractSeg works on FOD peaks, extract them
	sh2peaks $dwi_dir/wm_fod_norm.mif.gz $dwi_dir/wm_fod_norm_peaks.nii.gz -force -nthreads $nthreads
	
	# run TractSeg to get bundle segmentations
	TractSeg -i $dwi_dir/wm_fod_norm_peaks.nii.gz \
		 -o $out_dir --nr_cpus $nthreads \
		 --output_type tract_segmentation

	# and to get endings segmentation
	TractSeg -i $dwi_dir/wm_fod_norm_peaks.nii.gz \
		 -o $out_dir --nr_cpus $nthreads \
		 --output_type endings_segmentation
done < sublist.txt 
