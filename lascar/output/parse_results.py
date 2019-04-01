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

"""
parse_results.py

Implement function used by OutputMethod to interpret engines results.
"""

import itertools

import numpy as np


def apply_parse(engine, results):
    """
    Depending on the engine attribute 'output_parser_mode', apply_parse points toward the correct parse_output to apply on the engine results.
    And returns the parsed results.
    :param engine: the engine whose results need to be parsed
    :param results: the results to be parsed
    :return: the parsed results
    """

    if engine.output_parser_mode == "basic":
        return parse_output_basic(results)
    elif engine.output_parser_mode == "max":
        return parse_output_max(results, engine._guess_range)
    elif engine.output_parser_mode == "argmax":
        return parse_output_argmax(results, engine._guess_range)
    else:
        return None


def parse_output_basic(results):
    """
    parse_output_basic is the default output_parser.
    It takes as an input the results returned by an engine, and returns, for each row, basic statistic: [min, max, mean, var]
    :param results: the engine results to be parsed
    :return: the parsed results
    """
    if len(results.shape) == 1:
        return [(results.min(), results.max(), results.mean(), results.var())]
    else:
        return [(result.min(), result.max(), result.mean(), result.var()) for result in results]

def parse_output_max(results, guesses):
    """
    parse_output_max is the ouput_parser used on GuessEngines for which you want to maximize the results.
    (eg in Dpa, you want to extract the guess for which the result is the highest)

    For each guess, it outputs: (i,j,k) where:
    - i is the guess value
    - j is the max of the result for guess i
    - k is the rank of the guess i among all guesses

    :param results: the engine results to be parsed
    :param guesses: the engines guesses
    :return: the parsed results

    """
    if len(results.shape) == 2:
        scores = results.max(1)
    else:
        scores = results

    tmp = sorted(zip(guesses, scores), key=lambda x:x[1], reverse=True)
    return [ (s[0], s[1], rank+1) for rank, s in enumerate(tmp)] 


def parse_output_argmax(results, guesses):
    """
    parse_output_max is the ouput_parser used on GuessEngines for which you want to maximize the the absolute value of results.
    (eg in Cpa, you want to extract the guess for which the result is the highest, in absolute value)

    For each guess, it outputs: (i,j,k) where:
    - i is the guess value
    - j is the max of the absolute value of result for guess i
    - k is the rank of the guess i among all guesses

    :param results: the engine results to be parsed
    :param guesses: the engines guesses
    :return: the parsed results

    """

    if len(results.shape) == 2:
        scores = np.abs(results).max(1)
    else:
        scores = np.abs(results)

    tmp = sorted(zip(guesses, scores), key=lambda x:x[1], reverse=True)
    return [ (s[0], s[1], rank+1) for rank, s in enumerate(tmp)] 