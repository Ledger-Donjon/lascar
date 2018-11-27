"""
This file is part of lascar

lascar is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

"""

from math import ceil

import matplotlib.pyplot as plt

from . import OutputMethod
from .parse_results import apply_parse

import numpy as np


class MatPlotLibOutputMethod(OutputMethod):
    """
    MatPlotLibOutputMethod is an OutputMethod that will plot the  results from its tracked engines (at each output_step).

    If a filename is specified, the finalize() method will output all its parsed results inside a txt file.
    """

    def __init__(self, *engines, number_of_columns=None, number_of_rows=None, single_plot=False, display=True,
                 filename=None, legend=False):
        """

        :param engines: engines to be tracked
        :param number_of_columns: number of columns for multiplot
        :param number_of_rows: number of lines for multiplot
        :param single_plot: if True, all results are  on the same plot
        :param display: if true, display the plot on the screen
        :param filename: it set, save the figure to filename
        :param legend: it set, displays thee legend on the figure
        """
        if not len(engines):
            raise ValueError('MatPlotLibOutputMethod need engines to be instantiated...')

        OutputMethod.__init__(self, *engines)

        self.number_of_columns = number_of_columns
        self.number_of_rows = number_of_rows

        self.display = display
        self.filename = filename
        self.legend = legend

        if number_of_rows and number_of_columns and len(engines) > number_of_rows * number_of_columns:
            raise ValueError(
                "Wrong values for number_of_columns/number_of_rows considering the number of engines to display")

        if number_of_rows and not number_of_columns:
            self.number_of_columns = ceil(len(engines) / number_of_rows)
        if number_of_columns and not number_of_rows:
            self.number_of_rows = ceil(len(engines) / number_of_columns)

        self.single_plot = single_plot
        if single_plot:
            self.number_of_rows = 1
            self.number_of_columns = 1
        elif not number_of_columns and not number_of_rows:
            self.number_of_columns = min(4, len(engines)) if len(engines) else 4
            self.number_of_rows = max(1,ceil(len(engines) / 4))

    def _update(self, engine, results):

        try:
            idx = self.engines.index(engine) + 1
        except:
            idx = self.engines.index(engine.name) + 1

        if not self.single_plot:
            plt.subplot(self.number_of_rows, self.number_of_columns, idx)
            plt.title(engine.name)

        if isinstance(results, np.ndarray) and len(results.shape) == 1:
            plt.plot(results, label=engine.name)

        elif isinstance(results, np.ndarray) and len(results.shape) == 2:

            plt.plot(results.T)

            if hasattr(engine, 'solution') and engine.solution is not None:
                plt.plot(results[engine.solution], 'r-x', linewidth=2)

        else:
            self.logger.warning("Engine %s: cannot be used with MatPlotLibOutputMethod" % (
                engine.name))
            return


    def _finalize(self):
        if self.legend:
            plt.legend()

        if self.filename:
            plt.savefig(self.filename)
        if self.display:
            plt.show()


    def from_output_method(self, output_method):
        pass


class ScoreProgressionOutputMethod(MatPlotLibOutputMethod):
    """
    ScoreProgressionOutputMethod is an OutputMethod that will plot the progression of the results for one (or several) GuessEngine, along all output_steps.

    Quite close from MatplotlibOutputMethod, for the constructor arguments, ProgressionOuputMethod will display a figure at the finalize() step instead of at all output_steps

    For more info about parsing results, see lascar/ouput/parse_results


    """

    def __init__(self, *engines, number_of_columns=None, number_of_rows=None, single_plot=False, display=True,
                 filename=None, legend=False, filters=None):
        """

        :param engines: engines to be tracked
        :param number_of_columns: number of columns for multiplot
        :param number_of_rows: number of lines for multiplot
        :param single_plot: if True, all results are  on the same plot
        :param display: if true, display the plot on the screen
        :param filename: if set, save the figure to filename
        :param legend: if set, displays thee legend on the figure
        :param filters: if set, specify which guess is displayed for each attack. filters must be a list of len(engines) list of guesses

        """

        MatPlotLibOutputMethod.__init__(self, *engines, number_of_columns=number_of_columns,
                                        number_of_rows=number_of_rows, single_plot=single_plot, display=display,
                                        filename=filename, legend=legend)

        self.steps = []
        self.scores = {}
        self.scores_solution = {}

        if filters is None or (isinstance(filters, list) and len(filters) == len(engines) and all(
                [isinstance(i, list) for i in filters])):
            self.filters = filters  # filter is a list of len(engines) list...
        else:
            raise ValueError('filters must be a list of len(engines) list of guesses.')

    def _update(self, engine, results):

        results_parsed = apply_parse(engine, results)
        if results_parsed is None:
            return

        if engine.output_parser_mode in ['max', 'argmax']:
            if engine._number_of_processed_traces not in self.steps:
                self.steps.append(engine._number_of_processed_traces)

            if not engine.name in self.scores:
                self.scores[engine.name] = []
                self.scores_solution[engine.name] = []

            self.scores[engine.name].append([i[1] for i in results_parsed])

            if engine.solution is not None:
                self.scores_solution[engine.name].append(results_parsed[engine.solution][1])

    def _finalize(self):

        if not self.filename and not self.display:
            return self.steps, self.scores, self.scores_solution

        for i, engine_name in enumerate(self.scores):
            if not (self.number_of_rows == 1 and self.number_of_columns == 1):

                plt.subplot(self.number_of_rows, self.number_of_columns, i + 1)
                plt.title(engine_name)

            if self.filters is None:
                for j in range(len(self.scores[engine_name][0])):
                    plt.plot(self.steps, [self.scores[engine_name][k][j] for k in range(len(self.scores[engine_name]))],
                             label="%s guess %d" % (engine_name, j))
                try:
                    plt.plot(self.steps, self.scores_solution[engine_name], '-rx', linewidth=2)
                except:
                    pass

            else:
                for j in self.filters[i]:
                    plt.plot(self.steps, [self.scores[engine_name][k][j] for k in range(len(self.scores[engine_name]))],
                             label="%s guess %d" % (engine_name, j))

            plt.xlabel("number of traces")
            if self.legend:
                plt.legend()

        if self.filename:
            plt.savefig(self.filename)

        if self.display:
            plt.show()
            return self.steps, self.scores, self.scores_solution

    def get_steps(self):
        return self.steps

    def get_scores(self):
        return self.scores

    def get_scores_solution(self):
        return self.scores_solution




class RankProgressionOutputMethod(ScoreProgressionOutputMethod):
    """
    RankProgressionOutputMethod is an OutputMethod that will plot the progression of the ranks for one (or several) GuessEngine, along all output_steps.

    Quite close from MatplotlibOutputMethod, for the constructor arguments, RankOuputMethod will display a figure at the finalize() step instead of at all output_steps

    For more info about parsing results, see lascar/ouput/parse_results

    """

    def _update(self, engine, results):

        results_parsed = apply_parse(engine, results)
        if results_parsed is None:
            return

        if engine.output_parser_mode in ['max', 'argmax']:
            if engine._number_of_processed_traces not in self.steps:
                self.steps.append(engine._number_of_processed_traces)

            if not engine.name in self.scores:
                self.scores[engine.name] = []
                self.scores_solution[engine.name] = []

            self.scores[engine.name].append([i[2] for i in results_parsed])

            if engine.solution is not None:
                self.scores_solution[engine.name].append(results_parsed[engine.solution][2])
