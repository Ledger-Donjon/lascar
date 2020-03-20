import numpy as np

"""
RankEstimation implements an algorithm proposed here https://eprint.iacr.org/2014/920.pdf
It takes as an input an array p of probabilities for each engine and guess,
the real key and a parameter binWidth, controling the accuracy of the estimation.
It outputs the lower bound, estimated rank and upper bound
:param p: probabilities of each guess and engines
:param key_real: the real key
:param binWidth: parameter controlling the accuracy
:return: (lower bound, estimated rank, upper bound)

"""
def RankEstimation(p, key_real, binWidth):
    q=np.log(p)
    q=np.nan_to_num(q,neginf=-100)# requires numpy version 1.17 or newer!!! but makes the algorithm more stable
    subkeyNum = p.shape[0]
    histMin = 0
    y = np.array(1, dtype=np.float64)
    #Convolve the histograms
    for subkeyNo in range(subkeyNum):
        maxi, mini = np.max(q[subkeyNo]), np.min(q[subkeyNo])
        bins = max(int(np.ceil((maxi-mini)/binWidth)),1)
        maxi = mini + bins*binWidth #ensures equal binsize across histograms
        hist, edges = np.histogram( q[subkeyNo], bins=bins, range=(mini,maxi))
        histMin = histMin + edges[0]
        y = np.convolve(y, hist)
    #calculate bin number of the real key
    binNoReal = 0
    for subkeyNo in range(subkeyNum):
        candNo = key_real[subkeyNo]
        binNoReal = binNoReal + q[subkeyNo, candNo]
    binNoReal = int(( binNoReal - histMin ) / binWidth)

    binNoMax = max(0,binNoReal-subkeyNum)
    keyRankMax = np.sum(y[binNoMax:])

    binNoMin = binNoReal+subkeyNum
    keyRankMin = np.sum(y[binNoMin:])

    binNoEst = binNoReal
    keyRankEst = np.sum(y[binNoEst:])

    return keyRankMin, keyRankEst, keyRankMax


if __name__ == "__main__":
    p=np.array([[0.8,0.1,0.1], [0.5,0.3,0.2]])
    print(RankEstimation(p, [0,1], 0.1))
