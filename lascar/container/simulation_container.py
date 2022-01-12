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
simulation_container.py
"""
import numpy as np

from lascar.tools.aes import sbox, Aes
from lascar.tools.leakage_model import HammingPrecomputedModel
from .container import AbstractContainer, Trace

DEFAULT_KEY = [i for i in range(16)]


class BasicAesSimulationContainer(AbstractContainer):
    """
    BascAesSimulationContainer is an AbstractContainer used to naively
    simulate traces during the first Subbyte of the first round of an AES.
    """

    def __init__(
        self,
        number_of_traces,
        noise=1,
        key=DEFAULT_KEY,
        seed=1337,
        leakage_model="default",
        additional_time_samples=10,
        **kwargs
    ):
        """
        Basic constructor:

        :param number_of_traces:
        :param noise: noise level of the simulated noise. (The noise follows a normal law with mean zero, and std=noiselevel)
        :param key: optional, the key used during AES first round (16 bytes)
        :param seed: optional, the seed used to generate values and noise (for reproductibility)
        :param leakage_model: optional, leakage model used (HammingWeight by default)
        :param additional_time_samples: optional: add dummy time samples
        """

        if leakage_model == "default":
            leakage_model = HammingPrecomputedModel()

        self.seed = seed
        self.noise = noise

        self.leakage_model = leakage_model
        self.additional_time_samples = additional_time_samples

        self.value_dtype = np.dtype(
            [("plaintext", np.uint8, (16,)), ("key", np.uint8, (16,)),]
        )

        self.key = key

        AbstractContainer.__init__(self, number_of_traces, **kwargs)

        self.logger.debug("Creating BasicAesSimulationContainer.")
        self.logger.debug("Noise set to %f, seed set to %d.", self.noise, self.seed)
        self.logger.debug("Key set to %s", str(key))

    def generate_trace(self, idx):
        np.random.seed(seed=self.seed ^ idx)  # for reproducibility

        value = np.zeros((), dtype=self.value_dtype)
        value["plaintext"] = np.random.randint(0, 256, (16,), np.uint8)
        value["key"] = self.key

        leakage = np.random.normal(0, self.noise, (16 + self.additional_time_samples,))
        leakage[:16] += np.array(
            [
                self.leakage_model(sbox[value["plaintext"][i] ^ value["key"][i]])
                for i in range(16)
            ]
        )
        return Trace(leakage, value)


class AesSimulationContainer(AbstractContainer):
    """
    AesSimulationContainer is an AbstractContainer used to 
    simulate traces during all the round function of an AES.
    """

    def __init__(
        self,
        number_of_traces,
        noise=1,
        key=DEFAULT_KEY,
        seed=1337,
        leakage_model="default",
        additional_time_samples=10,
        **kwargs
    ):
        """
        Basic constructor:

        :param number_of_traces:
        :param noise: noise level of the simulated noise. (The noise follows a normal law with mean zero, and std=noiselevel)
        :param key: optional, the key used during AES first round (16 bytes)
        :param seed: optional, the seed used to generate values and noise (for reproductibility)
        :param leakage_model: optional, leakage model used (HammingWeight by default)
        :param additional_time_samples: optional: add dummy time samples
        """

        if leakage_model == "default":
            leakage_model = HammingPrecomputedModel()

        self.seed = seed
        self.noise = noise

        self.leakage_model = leakage_model
        self.additional_time_samples = additional_time_samples

        self.value_dtype = np.dtype(
            [
                ("plaintext", np.uint8, (16,)),
                ("key", np.uint8, (len(key),)),
                ("ciphertext", np.uint8, (16,)),
            ]
        )

        self.key = key

        AbstractContainer.__init__(self, number_of_traces, **kwargs)

        self.logger.debug("Creating AesSimulationContainer.")
        self.logger.debug("Noise set to %f, seed set to %d.", self.noise, self.seed)
        self.logger.debug("Key set to %s", str(key))

    def generate_trace(self, idx):
        np.random.seed(seed=self.seed ^ idx)  # for reproducibility

        value = np.zeros((), dtype=self.value_dtype)
        value["plaintext"] = np.random.randint(0, 256, (16,), np.uint8)
        value["key"] = self.key

        leakage = Aes.encrypt_keep_iv(value["plaintext"], Aes.key_schedule(value["key"]))
        value["ciphertext"] = leakage[-16:]


        leakage = np.array([self.leakage_model(i) for i in leakage]) # leakage model
        leakage = leakage + np.random.normal(0, self.noise, (len(leakage),)) # noise

        return Trace(leakage, value)

# class FromFunctionSimulationContainer(AbstractContainer):
#     """
#     FromFunctionSimulationContainer is a SimulationContainer which use a function to generate its trace.
#     The function can handle oscilloscopes, dut, or generated data.
#     To use in combination with Container.export methods
#     """
#     def __init__(self, number_of_traces, function):
#         """
#
#         :param number_of_traces:
#         :param function: function to generate the Traces. Must return a couple (leakage,value)
#         """
#         AbstractContainer.__init__(self, number_of_traces)
#
#         self._function = function
#         self.logger.debug('Creating ScopeDutSimulationContainer.')
#
#     def generate_trace(self, idx):
#         return self._function(idx)
