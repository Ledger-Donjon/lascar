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

import logging.handlers

# Create a common logger for the whole package
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# formatter: how the log will be formatted:
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# Write logs on stdout
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handle runtime warnings with a user-controlled behaviour
import numpy as np


def error_handler(error_type, flag):
    print("{} (flag: {}) encountered.".format(error_type, flag))
    if input("Abort (q) or ignore for this session (press enter) ?") == "q":
        raise Exception("Abort.")
    else:
        np.seterr(divide="warn")
        np.seterrcall(error_handler)


np.seterr(divide="call")
np.seterrcall(error_handler)

# Write logs to a rotating logfile
# rotating_file_handler = logging.handlers.RotatingFileHandler("lascar.log", maxBytes=1e6, backupCount=0)
# rotating_file_handler.setFormatter(formatter)
# logger.addHandler(rotating_file_handler)

from .session import Session
from .engine import *
from .container import *
from .output import *
from .tools.leakage_model import *
from .tools.processing import *
