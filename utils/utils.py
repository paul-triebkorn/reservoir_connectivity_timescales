from easyesn import PredictionESN
import numpy as np
import pyvista as pv

def shuffle_connectome(connectome, seed=1):
    np.random.seed(seed)
    r,c = np.triu_indices_from(connectome, k=1)
    rc = np.stack((r,c))

    connectome_triu = np.zeros_like(connectome)
    idx = np.arange(rc.shape[1])
    np.random.shuffle(idx)
    rc_shuffled = rc[:,idx]
    connectome_triu[r,c] = connectome[rc_shuffled[0],rc_shuffled[1]]
    connectome_shuffled = connectome_triu + connectome_triu.T
    return connectome_shuffled

def create_connectome_mask(network_name, connectome_labels):
    if network_name == "All":
        return np.ones((connectome_labels.shape[0]), dtype=bool)
    
    elif network_name == "auditory_custom":
        return_mask = np.zeros((connectome_labels.shape[0]), dtype=bool)
        connectome_labels = list(connectome_labels)
        for name in ["17Networks_RH_TempPar_4", "17Networks_RH_SomMotB_S2_1","17Networks_RH_TempPar_2", "17Networks_RH_TempPar_5", "17Networks_RH_TempPar_8",
                    "17Networks_LH_DefaultB_Temp_5", "17Networks_LH_SomMotB_Aud_1", "17Networks_LH_TempPar_3", "17Networks_LH_SomMotB_Aud_7", "17Networks_LH_SomMotB_Aud_2"]: # "17Networks_LH_DefaultB_PFCd_1"]:
            return_mask[connectome_labels.index(name)] = True   
        return return_mask
    
    elif network_name == "auditory":
        return_mask = np.zeros((connectome_labels.shape[0]), dtype=bool)
        for name in ["Aud","aud_"]:
            mask = [True if name in label else False for label in connectome_labels]
            return_mask[mask] = True   
        return return_mask
    
    elif network_name == "subcortex":
        return_mask = np.zeros((connectome_labels.shape[0]), dtype=bool)
        for name in ["Cerebellum-Cortex","Thalamus","Caudate","Putamen","Pallidum",'Hippocampus','Amygdala','Accumbens-area']:
            mask = [True if name in label else False for label in connectome_labels]
            return_mask[mask] = True   
        return return_mask
    else:
        return np.array([True if network_name in label else False for label in connectome_labels])    


def get_reservoir_timeconstants_input_mask(seed_reps, connectome, x_train, y_train, test_data_intact, test_data_shifted,
                                input_mask, leakingRate = 0.1, inputScaling=1):

    timeconstants = np.zeros((seed_reps, connectome.shape[0]))

    for c, res_seed in enumerate(range(seed_reps)):
        # print(" **************** reservoir seed %d  *************" % (res_seed))
        np.random.seed(res_seed)
        # set up the reservoir
        esn = PredictionESN(n_input=x_train.shape[1], n_output=x_train.shape[1], n_reservoir=connectome.shape[0], 
                            leakingRate=leakingRate, regressionParameters=[1e-2], solver="lsqr", 
                            reservoirDensity=1, feedback=False, inputScaling = inputScaling)
    
        esn._WOut = np.zeros((x_train.shape[1], 1 + x_train.shape[1] + connectome.shape[0]))

        # modify input weights of the reservoir such that only certain brain regions receive an input
        esn._createInputMatrix()
        esn._WInput[~input_mask,:] = 0
       
        # use the connectome to change the weights (_W) of the reservoir
        esn._W = connectome

        # run the reservoir for intact 
        _, reservoirStatesBuffer1  = esn.predict(test_data_intact)
        reservoirStatesBuffer1 = reservoirStatesBuffer1[101:,:]

        # now run reservoir for shifted version
        _, reservoirStatesBuffer2  = esn.predict(test_data_shifted)
        reservoirStatesBuffer2 = reservoirStatesBuffer2[101:,:]

        # begin the calculation of the narrative processing time constant
        begin = 433 # why these indices ? -> begin of same data in test_data_intact/shifted
        data  = reservoirStatesBuffer1[:,begin:] - reservoirStatesBuffer2[:,begin:]
        # calculate the alignment time:  data(neurons,time)
        # interate over reservoir neuron
        for neuron in range(data.shape[0]):
            max = abs(data[neuron,0])
            half_max = np.where(abs(data[neuron,:]) < max/2)[0]
            if len(half_max) == 0: # reservoir neuron hasn't reach half max yet, assign highest possible value
                timeconstants[c,neuron] = data.shape[1]
            else:
                timeconstants[c,neuron] = half_max[0]
            
    return timeconstants, reservoirStatesBuffer1, reservoirStatesBuffer2