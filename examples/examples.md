# Examples


## Base

In this folder we show how to use lascar to mount basics side-channel analysis. Most of these basic examples uses `BasicAesSimulationContainer`, a lascar container designed to generate simulated side-channel traces resulting from the first Subbyte of the first round of an AES.

- [snr.py](base/snr.py): perform leakage characterization (basic SNR) on AES simulated traces
- [ttest.py](base/ttest.py): perform leakage assesment (Welsh's ttest) on AES simulated traces
- [cpa.py](base/cpa.py): perform Correlation Power Analysis Attack on AES simulated traces
- [cpa-with-partition.py](base/cpa-with-partition.py): Same as cpa, but with a computational trick
- [profiled-attack.py](base/profiled-attack.py): perform a profiled attack using  both sklearn statistical classifiers and keras neural networks.
- [cpa-second-order.py](base/cpa-second-order.py): perform second order Correlation Power Analysis Attack on masked AES sbox simulation.
- [cpa-full-ranks.py](base/cpa-full-ranks.py): perform a cpa and plot the estimated rank of the complete key.

## ASCAD

In this folder, we use real traces of a secure AES implementation on a on the ATMega8515 provided by ANSSI at [ASCAD](https://github.com/ANSSI-FR/ASCAD). The idea is to reproduce with *lascar* the study made in their [paper](https://eprint.iacr.org/2018/053.pdf).

- [00-download-data.py](ascad/00-download-data.py): script to download and extract the traces provided by ANSSI
- [01-handle-data.py](ascad/01-handle-data.py): show how to use the downloaded traces with lascar
- [02-snr.py](ascad/02-snr.py): Use lascar to compute the 5 Signal-to-Noise Ratios (SNRs) described in chapter 2.5.2 of [ASCAS paper](https://eprint.iacr.org/2018/053.pdf).
- [03-keras-train.py](ascad/03-keras-train.py): Launch the profiling phase using keras neural network (first step of a profiling attack)
- [04-keras-test.py](ascad/04-keras-test.py): Launch the matching phase using keras neural network (second step of a profiling attack)
- [05-cpa-high-order.py](ascad/05-cpa-high-order.py): Perform a 2nd order CPA on ASCAD traces for a key recovery.

## rainbow

In this folder we use [rainbow](https://github.com/Ledger-Donjon/rainbow), our code emulation tool to emulate side-channel traces from a arm compiled .elf file.


## scaffold

TBP
