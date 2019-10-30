# This file is part of lascar
#
# lascar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelextrema


def find_offsets_inside_rectangle(trace, condition, width, ratio=1.0, separation=1):
    """
    Finds offsets inside trace which fits a condition (boolean function), during a given width.

    ratio is for ghost peaks correction

    separation is used to bypass adjacent patterns
    """
    count = 0
    offsets = []
    ratio_width = width * ratio
    condition_trace = condition(trace)

    i = 0
    while i < condition_trace.size:
        if condition_trace[i]:
            count = count + 1

        else:
            if count > ratio_width:
                offsets.append(i - count)
                i += separation
            count = 0
        i += 1
    return offsets


def smooth(x, window_len=11, window="hanning"):
    """smooth the data using a window with requested size.

     From https://scipy-cookbook.readthedocs.io/items/SignalSmooth.html

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman' (flat window will produce a moving average smoothing.)

    output:
        the smoothed signal
    """
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    if window_len < 3:
        return x
    if not window in ["flat", "hanning", "hamming", "bartlett", "blackman"]:
        raise ValueError(
            "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
        )

    s = np.r_[2 * x[0] - x[window_len - 1 :: -1], x, 2 * x[-1] - x[-1:-window_len:-1]]
    if window == "flat":  # moving average
        w = np.ones(window_len, "d")
    else:
        w = eval("np." + window + "(window_len)")

    y = np.convolve(w / w.sum(), s, mode="same")
    return y[window_len : -window_len + 1]


def plot_with(trace, idx, plot=True):
    _ = plt.plot(trace)
    _ = plt.plot(idx, trace[idx], "rx")
    if plot:
        plt.show()


def get_extrema_window(
    data, threshold, window_len=None, comparator=np.greater, plot=False
):
    """
    extract, from 'data', all the samples where there are local extrema with values > 'threshold'.
    (the comparator can be set with np.greater, np.less,...)
    If 'window_len' is set, will only ouptut the maximum value within '[ extrema - window_len/2, extrema + window_len/2] '
    """
    extrema = argrelextrema(data, comparator)[0]
    extrema_threshold = extrema[np.where(comparator(data[extrema], threshold))]

    if window_len and len(extrema_threshold) != 0:
        extrema_threshold_window = [extrema_threshold[0]]
        for i in extrema_threshold:
            if i - extrema_threshold_window[-1] < window_len and comparator(
                data[i], data[extrema_threshold_window[-1]]
            ):
                extrema_threshold_window[-1] = i
            if i - extrema_threshold_window[-1] >= window_len:
                extrema_threshold_window.append(i)
        extrema_threshold = np.array(extrema_threshold_window)

    if plot:
        plt.subplot(211)
        plot_with(data, extrema_threshold, plot=False)
        plt.subplot(212)
        plt.title("%d offsets found" % len(extrema_threshold))
        plt.plot(np.diff(extrema_threshold), "-x")
        plt.show()

    return extrema_threshold


def running_max(x, window=32):
    """
    Returns max of consecutive windows of x, each max repeated window times
    """
    n = x.shape[0]
    L = np.zeros(n, dtype=x.dtype)
    for i in range(0, n - window, window):
        L[i : i + window] = np.repeat(x[i : i + window].max(), window)
    leftover = n % window
    if leftover:
        L[-leftover:] = np.repeat(x[-leftover:].max(), leftover)
    return L


def running_min(x, window=32):
    """
    Returns min of consecutive windows of x, each max repeated window times
    """
    n = x.shape[0]
    L = np.zeros(n, dtype=x.dtype)
    for i in range(0, n - window, window):
        L[i : i + window] = np.repeat(x[i : i + window].min(), window)
    leftover = n % window
    if leftover:
        L[-leftover:] = np.repeat(x[-leftover:].min(), leftover)
    return L
