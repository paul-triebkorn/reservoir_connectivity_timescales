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

import socket
hostname = socket.gethostname();
host_id = {"posterior2":0, "EPINOV5":1}[hostname]

# %%
parcellation = "Schaefer2018_1000Parcels_17Networks"
project_dir = Path("/data2/pt_data/")
sublist = np.genfromtxt(str(project_dir/"scripts"/"sublist.txt"), dtype=str)
sublist = np.array_split(sublist,2)[host_id]
input_network_names = ["auditory_custom","auditory"]
BOIs = ["None","IFO","ILF","MLF","SLF_I","SLF_II","SLF_III","UF","AF",'CC']
LESIONS = ["bilateral","_right","_left"]

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
    connectome_weights = np.genfromtxt(str(project_dir/subject/"T1w"/"Diffusion"/f"weights_{parcellation}_15M.txt"))
    connectome_weights = np.log(connectome_weights+1)
    spectral_radius = np.linalg.eig(connectome_weights)[0][0] # divide by largest eigenvalue, such that spectral radius of connectome is 1
    connectome_weights_norm = connectome_weights/spectral_radius
    connectome = connectome_weights_norm * a

    timeconstants = np.zeros((len(LESIONS), len(input_network_names),len(BOIs), n_random_seed, connectome_weights_norm.shape[0]))

    # loop across lesions
    for lesion_idx, lesion in enumerate(LESIONS):
        # loop across input networks
        for in_net_idx, in_net in enumerate(input_network_names):
            print(in_net)
            input_mask = create_connectome_mask(in_net, connectome_labels)

            # loop across bundles of interest
            for boi_idx, boi in enumerate(BOIs):  
                # introduce lesion
                truncated_weights = connectome.copy()

                if boi == "CC": # remove all inter hemispheric connections
                    truncated_weights[0:500,500:1000] = 0 
                    truncated_weights[500:1000,0:500] = 0 
                    truncated_weights[0:500,1009:]    = 0
                    truncated_weights[1009:,0:500]    = 0
                    truncated_weights[500:1000,1000:1008] = 0
                    truncated_weights[1000:1008,500:1000] = 0
                    truncated_weights[1000:1008,1009:] = 0
                    truncated_weights[1009:,1000:1008] = 0

                elif not boi == "None":
                    if lesion == "bilateral":
                        HEMIS = ["_right","_left"]
                    else :
                        HEMIS = [lesion]

                    for hemi in HEMIS:
                        bundle_weights = np.genfromtxt(str(project_dir/subject/"T1w"/"Diffusion"/"TractSeg"/
                                                            "tck_segmentations"/f"bundle_connectome_{boi}{hemi}_weights_{parcellation}.txt"))
                        truncated_weights[bundle_weights > 0] = 0
                                    
                timeconstants[lesion_idx, in_net_idx, boi_idx, :, :], _, __ = get_reservoir_timeconstants_input_mask(n_random_seed, truncated_weights, x_train, y_train, test_data_intact, test_data_shifted, input_mask, leakingRate=lr, inputScaling=inputScaling)
        
    np.savez_compressed(str(subj_data_dir/f"timeconstants_{parcellation}_auditory_1000P.npz"), 
                                                                timeconstants   = timeconstants,
                                                                input_network_names = input_network_names,
                                                                BOIs = BOIs,
                                                                LESIONS = LESIONS,
                                                                spectral_radius = a,
                                                                leakingRate     = lr,
                                                                inputScaling    = inputScaling)

with Pool(processes=50) as p:
    res = p.map(run_subject, sublist)

