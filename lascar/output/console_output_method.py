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

from . import OutputMethod
from .parse_results import apply_parse


class ConsoleOutputMethod(OutputMethod):
    """
    ConsoleOuptputMethod is an OutputMethod that will display on the terminal the  parsed results from its tracked engines (for each output_step).

    For more info about parsing results, see lascar/ouput/parse_results

    If a filename is specified, the finalize() method will output all its parsed results inside a txt file.
    """

    def __init__(self, *engines, filename=None, max_guesses=3):
        """
        :param engines: the engines to be tracked
        :param filename: optional, if specified, the parsed results will be stored inside a txt file
        :param max_guesses: optional, when dealing with GuessEngine, specify the number of guesses to be dealt
        """
        OutputMethod.__init__(self, *engines)
        self.result = "\n"
        self.filename = filename
        self.max_candidates = max_guesses

    def _update(self, engine, results):

        results_parsed = apply_parse(engine, results)
        if results_parsed is None:
            return

        res_str = '%s with %d traces: ' % (engine.name, engine._number_of_processed_traces)

        if engine.output_parser_mode == "basic":
            res_str += ' %s' % results_parsed

        else:

            max_candidates = min(engine._number_of_guesses, self.max_candidates)

            ranks = [r[2] for r in results_parsed]
            indexes = [ranks.index(i + 1) for i in range(max_candidates)]

            res_str += ' - '.join("[{:>02x}] {:>4.2f} (rank {})".format(*results_parsed[i]) for i in indexes)

        self.logger.info("Results: " + res_str)
        self.result += res_str + '\n'

    def finalize(self):
        if self.filename is not None:
            with open(self.filename, "w") as file:
                file.write(self.result)
        else:
            self.logger.debug("Results: " + self.result)

        return self.result
