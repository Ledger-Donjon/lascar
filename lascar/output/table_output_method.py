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
# Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Adrian Thillard, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr, adrian.thillard@ledger.fr

from .import OutputMethod
from .parse_results import apply_parse

class TableOutputMethod(OutputMethod):
    """
    TableOutputMethod is an OutputMethod that will display a table of the ranked results
    """

    def __init__(self, *engines, filename=None, max_guesses=10):
        """
        :param engines: the engines to be tracked
        :param filename: optional, if specified, the parsed results will be stored inside a txt file
        :param max_guesses: optional, when dealing with GuessEngine, specify the number of guesses to be dealt
        """
        OutputMethod.__init__(self, *engines)
        self.filename = filename
        self.max_candidates = max_guesses
        self.best_guesses={}
        self.engine_names = []


    def _update(self, engine, results):

        results_parsed = apply_parse(engine, results)

        if results_parsed is None:
            return

        if not engine.name in self.best_guesses:
            self.logger.info(engine.name)
            self.best_guesses[engine.name] = []
            self.engine_names += [engine.name]
        
        
        if engine.output_parser_mode == "basic":
            self.best_guesses[engine.name].append(results_parsed)

        else:

            max_candidates = min(engine._number_of_guesses, self.max_candidates)

            ranks = [r[2] for r in results_parsed]
            indices = [ranks.index(i + 1) for i in range(max_candidates)]

            self.best_guesses[engine.name].append([results_parsed[i] for i in indices])
            

    def finalize(self):
        row_format ="{:>10}" * (len(self.engine_names)+1)
        line_separator = "="*10*(len(self.engine_names)+1)+"\n"
        result = row_format.format("",*(self.engine_names))
        result += "\n"
        result += line_separator
        for rank in range(self.max_candidates):
            row = [self.best_guesses[e.name][-1][rank][0] for e in self.engines]
            score_row = [round(self.best_guesses[e.name][-1][rank][1],3) for e in self.engines]
            prefix = "rank %i"%(rank+1)
            result+= row_format.format(prefix,*row)+"\n"
            result+= row_format.format("",*score_row)+"\n"
            result += line_separator

        if self.filename is not None:
            with open(self.filename, "w") as file:
                file.write(result)
        else:
            print(result)
                
        return self.best_guesses
