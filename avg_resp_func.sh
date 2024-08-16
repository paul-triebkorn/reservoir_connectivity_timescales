# execute the code only ones to generate the average response functions
# activate conda env
source /path/to/anaconda3/bin/activate
conda activate /path/to/anaconda3/envs/env_w_MRtrix

sublist_template="/path/to/scripts/sublist.txt"
avg_resp_dir="/path/to/scripts/"
responsemean `cat ${sublist_template} | xargs -I % echo /path/to/%/T1w/Diffusion/response_wm.txt` $avg_resp_dir/avg_response_wm.txt -force
responsemean `cat ${sublist_template} | xargs -I % echo /path/to/%/T1w/Diffusion/response_gm.txt` $avg_resp_dir/avg_response_gm.txt -force 
responsemean `cat ${sublist_template} | xargs -I % echo /path/to/%/T1w/Diffusion/response_csf.txt` $avg_resp_dir/avg_response_csf.txt -force
