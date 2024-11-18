import os
nthreads=1
os.environ["OMP_NUM_THREADS"] = str(nthreads)
os.environ["OPENBLAS_NUM_THREADS"] = str(nthreads)
os.environ["MKL_NUM_THREADS"] = str(nthreads)
os.environ["VECLIB_MAXIMUM_THREADS"] = str(nthreads)
os.environ["NUMEXPR_NUM_THREADS"] = str(nthreads)

import numpy as np
from pathlib import Path
from utils.utils import get_reservoir_timeconstants_input_mask, create_connectome_mask, shuffle_connectome
from multiprocess import Pool
from functools import partial
import bct

# get surface and annotation
n_parcels=1000
parcellation = f"Schaefer2018_{n_parcels}Parcels_17Networks"

project_dir = Path("/path/to/")
sublist = list(np.genfromtxt(str(project_dir/"sublist.txt"), dtype=str))

connectome_labels = list(np.genfromtxt(str(project_dir/"Schaefer_mrtrix_lut"/f"{parcellation}_order_LUT.txt"), skip_header=1, usecols=1, dtype=str))
connectome_labels.remove("Left-Thalamus-Proper")
connectome_labels.remove("Right-Thalamus-Proper")
connectome_labels = np.array(connectome_labels)

# load training and testing data for the reservoir
x_train = np.load(str(project_dir/"utils"/"data"/"in_small.npy"))
y_train = np.load(str(project_dir/"utils"/"data"/"out_small.npy"))
test_data_intact  = np.load(str(project_dir/"utils"/"data"/"NTF_intact_embeddings.npy"))
test_data_shifted= np.load(str(project_dir/"utils"/"data"/"NTF_shifted_embeddings.npy"))
n_random_seed=10

def run_subject(subject, in_net="Vis", mod_connectome=None, seed=1):    
    a = 0.8
    lr = 0.5
    inputScaling = 0.5

    # get full brain connectome and normalize it
    connectome_weights = np.genfromtxt(str(project_dir/subject/"T1w"/"Diffusion"/f"weights_{parcellation}_15M.txt"))
    connectome_weights = np.log(connectome_weights+1)
    spectral_radius = np.linalg.eig(connectome_weights)[0][0] # divide by largest eigenvalue, such that spectral radius of connectome is 1
    connectome_weights_norm = connectome_weights/spectral_radius

    if mod_connectome == "shuffle":
        null_weights = shuffle_connectome(connectome_weights_norm, seed)

    elif mod_connectome == "null_model_und_sign":
        null_weights, _ = bct.null_model_und_sign(connectome_weights_norm, 0, 0.1, seed=seed)

    elif mod_connectome == "randmio_und":
        null_weights, _ = bct.randmio_und(connectome_weights_norm, 1, seed=seed)

    elif mod_connectome == "latmio_und":
        dist_mat = np.genfromtxt(str(project_dir/subject/"T1w"/"Diffusion"/f"lengths_{parcellation}_15M.txt"))
        dist_mat[dist_mat==0] = 9999999999
        dist_mat[np.isnan(dist_mat)] = 9999999999
        _, null_weights, __, ___ = bct.latmio_und(connectome_weights_norm, 1, dist_mat, seed=seed)

    elif mod_connectome == "None":
        null_weights = connectome_weights_norm

    null_weights *= a
    input_mask = create_connectome_mask(in_net, connectome_labels)
    timeconstants, _, __ = get_reservoir_timeconstants_input_mask(n_random_seed, null_weights, x_train, y_train, test_data_intact, test_data_shifted, input_mask, leakingRate=lr, inputScaling=inputScaling)
    return timeconstants


in_net = "auditory_custom"
results_dir = Path(project_dir/"null_conn_timescale")

for mod in ["None", "shuffle", "null_model_und_sign", "randmio_und", "latmio_und"]:
    timeconstants_all = []
    with Pool(processes=50) as p:
        if mod == "None":
            timeconstants_all.append(p.map(partial(run_subject, **{"in_net": in_net, "mod_connectome" : mod}), sublist))
        else:
            for seed in np.arange(10):
                timeconstants_all.append(p.map(partial(run_subject, **{"in_net": in_net, "mod_connectome" : mod, "seed" : seed}), sublist))
    timeconstants_all = np.stack(timeconstants_all)
    np.savez_compressed(results_dir/f"timeconstants_{mod}.npz", timeconstants_all=timeconstants_all, in_net=in_net)
