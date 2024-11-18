# Intro
This repository contains the code to reproduce the results and findings of the article "Impact of white matter connectivity on brain network processing time scales – a computational connectomic study". 

# How to use:
<p> The following scripts are used to reconstruct the connectomes and identify single fibre bundles from the diffusion data of HCP subjects. Note, that in each script the root folder needs to be specified to point to the data and software required. <br>
Run in following order </p>

1. apply_schaefer_parc.sh
    * Projects the Schaefer2018_400Parcels_7Networks atlas onto the T1 image of each subjects
2. pre_avg_resp_func.sh
    * diffusion preprocessing
3. avg_resp_func.sh
    * response function averaging
3. post_avg_resp_func.sh
    * perform tractography
4. extract_connectome.sh
5. run_TractSeg.sh
    * estimate inclusion and exclusion masks for the fibre bundles of interest
6. run_TractSeg_extract_tck.sh
    * extract the tracts from the tractography given the inclusion and exclusion masks
7. run_TractSeg_extract_connectome_w_tck2connectome.sh
    * create bundle specific connectomes, given the Schaefer parcellation and the extracted tracts

<p>
To reproduce the results about alignment times in the EDR based resevoir (Figures 2, S1 and S2) run the code in run_EDR_reservoir_sweep_pathways.py. This does not require connectome data from any subject, but builds the connectome based on the exponential distance rule.
</p>

<p>
To reproduce the results about alignment times in human connectome model (Figures 3,4,5 and 6) run the code in timeconstants_task.py. 
</p>

<p>
To reproduce the results about alignment times in human connectome model and comparing it to the empirical ordering of alignment times (Figures 7 and 8) run the code in timeconstants_task_auditory_1000P.py. This requires to run the steps on connectome and fibre bundle extraction for the Schaefer 1000Parcels 17 Networks parcellation.  
</p>

# Software dependencies
* Freesurfer version 7.4.0
* FSL
* MRtrix 3.0.3
* TractSeg 2.7
* Python 3.10.4 with 
    * numpy
    * easyesn (NOTE: include this change in the easyesn code, https://github.com/kalekiu/easyesn/issues/12)
