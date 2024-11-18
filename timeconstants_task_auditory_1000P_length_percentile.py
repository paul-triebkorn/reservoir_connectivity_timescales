# %%
import os
nthreads=1
os.environ["OMP_NUM_THREADS"] = str(nthreads)
os.environ["OPENBLAS_NUM_THREADS"] = str(nthreads)
os.environ["MKL_NUM_THREADS"] = str(nthreads)
os.environ["VECLIB_MAXIMUM_THREADS"] = str(nthreads)
os.environ["NUMEXPR_NUM_THREADS"] = str(nthreads)

import numpy as np
from pathlib import Path
from utils.utils import get_reservoir_timeconstants_input_mask, create_connectome_mask
from multiprocess import Pool

# %%
parcellation = "Schaefer2018_1000Parcels_17Networks"
project_dir = Path("/data2/pt_data/")
sublist = np.genfromtxt(str(project_dir/"scripts"/"sublist.txt"), dtype=str)
input_network_names = ["auditory_custom","auditory"]
percentiles = np.arange(0,101,10)
short_long_list = ['short','long']

connectome_labels = list(np.genfromtxt(str(project_dir/"scripts"/"Schaefer_mrtrix_lut"/f"{parcellation}_order_LUT.txt"), skip_header=1, usecols=1, dtype=str))
connectome_labels.remove("Left-Thalamus-Proper")
connectome_labels.remove("Right-Thalamus-Proper")
connectome_labels = np.array(connectome_labels)

# load training and testing data for the reservoir
x_train = np.load(str(project_dir/"scripts"/"utils"/"data"/"in_small.npy"))
y_train = np.load(str(project_dir/"scripts"/"utils"/"data"/"out_small.npy"))
test_data_intact  = np.load(str(project_dir/"scripts"/"utils"/"data"/"NTF_intact_embeddings.npy"))
test_data_shifted= np.load(str(project_dir/"scripts"/"utils"/"data"/"NTF_shifted_embeddings.npy"))
n_random_seed=10

def run_subject(subject):
    subj_data_dir = project_dir/subject/"timeconstants_bundle_removal"
    subj_data_dir.mkdir(exist_ok=True)

    a = 0.8
    lr = 0.5
    inputScaling = 0.5
    

    # get full brain connectome and normalize it
    dist_mat = np.genfromtxt(project_dir/subject/"T1w"/"Diffusion"/f"lengths_{parcellation}_15M.txt")
    dist_mat_triu = dist_mat[np.triu_indices_from(dist_mat,1)]
    len_percentiles = np.percentile(dist_mat_triu[dist_mat_triu!=0], percentiles)
    len_percentiles[0] = 0   # 0% --> empty connectome
    len_percentiles[-1] += 1 # 100% --> full connectome

    
    connectome_weights = np.genfromtxt(str(project_dir/subject/"T1w"/"Diffusion"/f"weights_{parcellation}_15M.txt"))
    connectome_weights = np.log(connectome_weights+1)
    spectral_radius = np.linalg.eig(connectome_weights)[0][0] # divide by largest eigenvalue, such that spectral radius of connectome is 1
    connectome_weights_norm = connectome_weights/spectral_radius
    connectome = connectome_weights_norm * a    
    timeconstants = np.zeros((len(input_network_names), len(percentiles), len(short_long_list), n_random_seed, connectome_weights_norm.shape[0]))
    
    for in_net_idx, in_net in enumerate(input_network_names):
        input_mask = create_connectome_mask(in_net, connectome_labels)
        for p_i, p in enumerate(len_percentiles):
            for sl_i, sl in enumerate(short_long_list):
                truncated_weights = connectome.copy()
                if sl == 'short':
                    truncated_weights[dist_mat<=p] = 0   
                elif sl == 'long':
                    truncated_weights[dist_mat>=p] = 0   
                timeconstants[in_net_idx, p_i, sl_i, :, :], _, __ = get_reservoir_timeconstants_input_mask(n_random_seed, truncated_weights, x_train, y_train, test_data_intact, test_data_shifted, input_mask, leakingRate=lr, inputScaling=inputScaling)
            
    np.savez_compressed(str(subj_data_dir/f"timeconstants_{parcellation}_auditory_1000P_len_perc.npz"), 
                                                                timeconstants   = timeconstants,
                                                                input_network_names = input_network_names,
                                                                len_percentiles = len_percentiles,
                                                                percentiles     = percentiles,
                                                                spectral_radius = a,
                                                                leakingRate     = lr,
                                                                inputScaling    = inputScaling)

with Pool(processes=50) as p:
    res = p.map(run_subject, sublist)