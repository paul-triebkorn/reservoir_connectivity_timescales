import numpy as np
from easyesn import PredictionESN


leak_rate = 0.2
gradient= 0.00075
gain = 1.75
grad2=1.25
breadth=600  
expon=3

in_small = np.load('utils/data/in_small.npy')
out_small = np.load('utils/data/out_small.npy')
inputDataTesting = np.load("utils/data/NTF_intact_embeddings.npy")
inputDataTesting2 = np.load("utils/data/NTF_shifted_embeddings.npy")

path_range = np.arange(0,901,50)
path_from, path_to = np.meshgrid(path_range, path_range)
from_to  = np.vstack((path_from[np.triu_indices_from(path_to,6)], 
                        path_to[np.triu_indices_from(path_to,6)])).T

for f,t in from_to:
    seed_reps = 40
    vectorDim = 100
    numNode = 1000
    timeconstants=np.zeros((seed_reps,numNode))

    for c, res_seed in enumerate(range(0,seed_reps)):
    # set the seed
        np.random.seed(res_seed)

        # set up the reservoir
        # leakingRate=0.2 changing too fast, mutliple with 0.05; changed
        esn = PredictionESN(n_input=vectorDim, n_output=vectorDim, n_reservoir=numNode, leakingRate=leak_rate, regressionParameters=[1e-2], solver="lsqr", feedback=False)

        # train the reservoir with a new seed
        esn.fit(in_small, out_small, transientTime="Auto", verbose=1)
        
        # modify the reservoir topology for input
        esn._WInput[300:,:] = 0

        # implement exponential distance rule on connectome
        temp_W = esn._W.copy()
        esn._W[:]=0
        for i in range(esn._W.shape[0]):
            for j in range(esn._W.shape[1]):
                if abs(i-j) <= breadth:
                    esn._W[i,j] = ((breadth-abs(i-j))/breadth)**expon*temp_W[i,j]* (1 + i * gradient)*gain
        
        # make _W symmetric
        esn._W += esn._W.T
        esn._W /= 2

        # here we determine if the white matter pathway to the late area is from an input driven or associatve area
        esn._W[f:f+100,t:t+100] = temp_W[f:f+100,t:t+100]*grad2
        esn._W[t:t+100,f:f+100] = temp_W[f:f+100,t:t+100].T*grad2 # make it symmetric

        # run the reservoir with intact ordering of input
        prediction,reservoirStatesBuffer1  = esn.predict(inputDataTesting)
        reservoirStatesBuffer1 = reservoirStatesBuffer1[101:,:]
        
        # run the reservoir with scrambled ordering of input
        prediction,reservoirStatesBuffer2  = esn.predict(inputDataTesting2)
        reservoirStatesBuffer2 = reservoirStatesBuffer2[101:,:]

        begin = 433 # begin of same data in test_data_intact/shifted
        data  = reservoirStatesBuffer1[:,begin:] - reservoirStatesBuffer2[:,begin:]
        # calculate the alignment time:  data(neurons,time)
        # interate over reservoir neuron
        for neuron in range(data.shape[0]):
            max = abs(data[neuron,0])
            idx = np.where(abs(data[neuron,:]) < max/2)[0]
            if len(idx) == 0 : # alignment wasn't reached yet
                timeconstants[c,neuron] = data.shape[1]
            else:
                timeconstants[c,neuron] = idx[0]
        
    np.savez_compressed(f"/path/to/EDR_reservoir/symm_EDR_pathway_from_{f}-{f+100}_to_{t}-{t+100}.npz", 
                                                                                connectome = esn._W, 
                                                                                input = esn._WInput, 
                                                                                timeconstants = timeconstants)


