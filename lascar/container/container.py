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
container.py
"""

import logging

import numpy as np

from collections import namedtuple

_Trace = namedtuple("Trace", ["leakage", "value"])


class Trace(_Trace):
    """
    Trace is the class to represent a side-channel trace (Trace in lascar),
    Genuinely, it is a tuple of two items:
    - The first item is "leakage" and represents the side-channel observable
    - The second item is "value" and represents the handled values during the observation of "leakage".

    The only restriction here is that "leakage" and "data" must be numpy.arrays of any shape.

    trace = (leakage, value) where leakage and value are numpy.arrays

    """

    def __new__(cls, *args):
        super_obj = super(_Trace, cls)

        if len(args) != 2:
            raise ValueError("Trace:  Only two arguments.")

        # if not isinstance(args[0], np.ndarray) or not isinstance(args[1], np.ndarray):
        #    raise ValueError("Trace: leakage and value must be numpy.ndarray.")

        return super_obj.__new__(cls, args)

    def __str__(self):
        return "Trace with leakage:[%s, %s] value:[%s, %s]" % (
            self.leakage.shape,
            self.leakage.dtype,
            self.value.shape,
            self.value.dtype,
        )

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join("{}=%r".format(name) for name in self._fields) % self,
        )

    def __eq__(self, other):
        return np.all(self.leakage == other.leakage) and np.all(
            self.value == other.value
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):

        if isinstance(other, Trace):
            return TraceBatchContainer(
                np.vstack([self.leakage, other.leakage])
                if len(self.leakage.shape) > 0
                else np.hstack([self.leakage, other.leakage]),
                np.vstack([self.value, other.value])
                if len(self.value.shape) > 0
                else np.hstack([self.value, other.value]),
            )
        if isinstance(other, TraceBatchContainer):
            return TraceBatchContainer(
                np.vstack(
                    [self.leakage, other.leakages]
                    if len(self.leakage.shape) > 0
                    else np.hstack([self.leakage, other.leakages])
                ),
                np.vstack([self.value, other.values])
                if len(self.value.shape) > 0
                else np.hstack([self.value, other.values]),
            )


class Container:
    """
    Container class is an abstact class used to represent Side-Channel traces.

    In lascar a trace is a couple (tuple) of a side-channel leakage associated to the values handled.

    trace = (leakage, value)

    Where both leakage and value can be represented as a numpy array.

    The role of the Container class is to be overloaded so that it can deliver traces, stored as a specified format.
    Mostly, the __getitem__/__setitem__ have to be overloaded when user want to write its own Container format class.

    :param number_of_traces:
    """

    def __init__(self, **kwargs):
        """
        Basic Constructor.

        To this point, child must implement leakages and values as np.array or AbstractArray
        """
        self.logger = logging.getLogger(__name__)

        if self.leakages.shape[0] != self.values.shape[0]:
            raise ValueError(
                "leakages and values dont share the same first dim (number_of_traces): %s %s"
                % (self.leakages.shape, self.values.shape)
            )

        self.number_of_traces_max = self.leakages.shape[0]

        self._leakage_base_abstract = AbstractArray(
            self.leakages.shape[1:], self.leakages.dtype
        )
        self._leakage_section_abstract = AbstractArray(
            self.leakages.shape[1:], self.leakages.dtype
        )
        self._leakage_abstract = AbstractArray(
            self.leakages.shape[1:], self.leakages.dtype
        )

        self._value_base_abstract = AbstractArray(
            self.values.shape[1:], self.values.dtype
        )
        self._value_section_abstract = AbstractArray(
            self.values.shape[1:], self.values.dtype
        )
        self._value_abstract = AbstractArray(self.values.shape[1:], self.values.dtype)

        self.number_of_traces = kwargs.get(
            "number_of_traces", self.number_of_traces_max
        )
        self.leakage_section = kwargs.get("leakage_section", None)
        self.value_section = kwargs.get("value_section", None)
        self.leakage_processing = kwargs.get("leakage_processing", None)
        self.value_processing = kwargs.get("value_processing", None)

    @property
    def leakage_section(self):
        """
        Leakage area to be read from the original leakage.

        :type: list, range, slice
        """
        return self._leakage_section if hasattr(self, "_leakage_section") else None

    @leakage_section.setter
    def leakage_section(self, section):
        self.logger.debug("Setting leakage_section to %s" % section)
        if self.leakage_processing is not None:
            self.logger.warning(
                "Since leakage_section is being set, leakage_processing is set to None."
            )
            self.leakage_processing = None

        if section is None:  # reset leakage_section and leakage_end
            self._leakage_section_abstract.update(self._leakage_base_abstract)
            self._leakage_abstract.update(self._leakage_base_abstract)

        else:
            try:
                leakage = self._leakage_base_abstract.zeros()[section]
                self._leakage_section_abstract.update(leakage)
                self._leakage_abstract.update(leakage)
            except:
                raise TypeError(
                    'Cant apply section "%s" to leakage of shape/dtype %s/%s'
                    % (
                        section,
                        self._leakage_base_abstract.shape,
                        self._leakage_base_abstract.dtype,
                    )
                )

        self._leakage_section = section

    @property
    def leakage_processing(self):
        """
        Leakage_processing. function applied upon the leakages after reading and
        leakage_section)

        :type: function (or callable) taking leakage[leakage_section] as an
            argument
        """
        return (
            self._leakage_processing if hasattr(self, "_leakage_processing") else None
        )

    @leakage_processing.setter
    def leakage_processing(self, processing):
        self.logger.debug("Setting leakage_processing to %s" % processing)

        if processing is None:
            self._leakage_abstract.update(self._leakage_section_abstract)

        else:
            try:
                leakage = processing(self._leakage_section_abstract.zeros())
                self._leakage_abstract.update(leakage)
            except:
                raise TypeError(
                    'Cant apply processing "%s" to leakage of shape/dtype %s/%s'
                    % (
                        processing,
                        self._leakage_base_abstract.shape,
                        self._leakage_base_abstract.dtype,
                    )
                )

        self._leakage_processing = processing

    def apply_leakage_section(self, leakages):
        if self.leakage_section is None:
            return leakages
        if self._leakage_base_abstract.shape == ():
            return leakages[self.leakage_section]
        return leakages[:, self.leakage_section]

    def apply_leakage_processing(self, leakages):
        if self.leakage_processing is None:
            return leakages
        if self._leakage_section_abstract.shape == ():  # 0D leakage
            return np.array([self.leakage_processing(l) for l in leakages])
        return np.apply_along_axis(self.leakage_processing, 1, leakages)

    def apply_both_leakage(self, leakages):
        return self.apply_leakage_processing(self.apply_leakage_section(leakages))

    @property
    def value_section(self):
        """
        Value area to be read from the original value.

        :type: list, range, slice
        """
        return self._value_section if hasattr(self, "_value_section") else None

    @value_section.setter
    def value_section(self, section):
        self.logger.debug("Setting value_section to %s" % section)
        if self.value_processing is not None:
            self.logger.warning(
                "Since value_section is being set, value_processing is set to None."
            )
            self.value_processing = None

        if section is None:  # reset value_section and value_end
            self._value_section_abstract.update(self._value_base_abstract)
            self._value_abstract.update(self._value_base_abstract)

        else:
            try:
                value = self._value_base_abstract.zeros()[section]
                self._value_section_abstract.update(value)
                self._value_abstract.update(value)
            except:
                raise TypeError(
                    'Cant apply section "%s" to value of shape/dtype %s/%s'
                    % (
                        section,
                        self._value_base_abstract.shape,
                        self._value_base_abstract.dtype,
                    )
                )

        self._value_section = section

    @property
    def value_processing(self):
        """
        Current value_processing. function applied upon the values after
        reading and value_section.

        :type: function (or callable) taking value[value_section] as an argument
        """
        return self._value_processing if hasattr(self, "_value_processing") else None

    @value_processing.setter
    def value_processing(self, processing):
        self.logger.debug("Setting value_processing to %s" % processing)

        if processing is None:
            self._value_abstract.update(self._value_section_abstract)

        else:
            try:
                value = processing(self._value_section_abstract.zeros())
                self._value_abstract.update(value)
            except:
                raise TypeError(
                    'Cant apply processing "%s" to value of shape/dtype %s/%s'
                    % (
                        processing,
                        self._value_base_abstract.shape,
                        self._value_base_abstract.dtype,
                    )
                )

        self._value_processing = processing

    def apply_value_section(self, values):
        if self.value_section is None:
            return values
        if self._value_base_abstract.shape == ():
            return values[self.value_section]
        return values[:, self.value_section]

    def apply_value_processing(self, values):
        if self.value_processing is None:
            return values
        if self._value_section_abstract.shape == ():  # 0D value
            return np.array([self.value_processing(v) for v in values])
        return np.apply_along_axis(self.value_processing, 1, values)

    def apply_both_value(self, values):
        return self.apply_value_processing(self.apply_value_section(values))

    def plot_leakage(self, key):
        from lascar.plotting import plot

        self.logger.debug("plot_leakage at index %s", key)

        plot([self[i].leakage for i in key])

    def __len__(self):
        return self.number_of_traces

    def __iter__(self):
        """
        Container is iterable
        It returns its trace during iteration.

        :return: Iterator over the container traces.
        """
        for i in range(len(self)):
            yield self[i]

    def __str__(self):
        res = "Container with %d traces. " % (self.number_of_traces)
        res += "leakages: %s, values: %s. " % (
            self._leakage_abstract,
            self._value_abstract,
        )
        if self.leakage_section is not None:
            res += "leakage_section set to %s. " % self.leakage_section
        if self.leakage_processing is not None:
            res += "leakage_processing set to %s. " % self.leakage_processing
        if self.value_section is not None:
            res += "value_section set to %s. " % self.value_section
        if self.value_processing is not None:
            res += "value_processing set to %s. " % self.value_processing

        return res

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for i in range(len(self)):
            if self[i] != other[i]:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_leakage_mean_var(self):
        """
        Compute mean/var of the leakage.
        :return: mean/var of the container leakages
        """
        from lascar import Session

        session = Session(self).run()
        return session["mean"].finalize(), session["var"].finalize()


# def to_trace(func):
#     def wrapper(*args, **kwargs):
#         result = func(*args, **kwargs)

#         if isinstance(result, Trace):
#             return result

#         try:
#             return Trace(result)
#         except:
#             raise TypeError("the output must be a 2-uple of numpy array: leakage,value.")
#         return result
#     return wrapper


class AbstractContainer(Container):
    """
    AbstractContainer is a Container class used when the side-channel traces are generated from functions.
    It can be used for instance:

    - setting up sitions with oscilloscope and DUT
    - when implementing Simulated traces
    """

    def __init__(self, number_of_traces, **kwargs):
        self.logger = logging.getLogger(__name__)

        trace = self.generate_trace(0)
        self.leakages = AbstractArray(
            (number_of_traces,) + trace.leakage.shape, trace.leakage.dtype
        )
        self.values = AbstractArray(
            (number_of_traces,) + trace.value.shape, trace.value.dtype
        )

        Container.__init__(self, **kwargs)

    def generate_trace(self, idx):
        """
        Generates a single trace indexed by an integer i
        (the i^th trace)

        Function to be overloaded

        :param idx: integer
        :return: a Trace
        """
        raise NotImplemented

    def generate_trace_batch(self, idx_begin, idx_end):
        """
        Generates a trace_batch of specified indexes
        """
        leakages = np.empty(
            (idx_end - idx_begin,) + self._leakage_abstract.shape,
            self._leakage_abstract.dtype,
        )
        values = np.empty(
            (idx_end - idx_begin,) + self._value_abstract.shape,
            self._value_abstract.dtype,
        )

        for i, j in enumerate(range(idx_begin, idx_end)):
            leakage, value = self.generate_trace(j)
            leakages[i] = leakage
            values[i] = value

        return TraceBatchContainer(leakages, values)

    def __getitem__(self, key):
        """
        :rtype: Trace or TraceBatch depending on key
        """
        self.logger.debug("__getitem__ with key %s" % str(key))

        if isinstance(key, int):
            leakage, value = self.generate_trace(key)
            leakage = self.apply_both_leakage(leakage.reshape((1,) + leakage.shape))[0]
            value = self.apply_both_value(value.reshape((1,) + value.shape))[0]
            return Trace(leakage, value)

        elif isinstance(key, slice):
            # check contiguity:
            if key.step is not None and key.step > 1:
                raise ValueError(
                    "AbstractContainer __getitem__ slice elements must be contiguous"
                )
            offset_begin = key.start if key.start else 0
            offset_end = key.stop if key.stop else self.number_of_traces

        elif isinstance(key, list):
            # check contiguity:
            if np.any(np.diff(np.array(key)) != 1):
                raise ValueError(
                    "AbstractContainer __getitem__ list elements must be contiguous"
                )
            offset_begin = key[0]
            offset_end = key[-1]
        else:
            raise ValueError(
                "AbstractContainer __getitem__ only accepts int, list and slices (contiguous)"
            )

        if (
            offset_begin < 0
            or offset_end <= offset_begin
            or offset_end > self.number_of_traces
        ):
            raise ValueError(
                "get_batch must have 0 <= offset_begin < offset_end must <= %d. Got (%d, %d)"
                % (self.number_of_traces, offset_begin, offset_end)
            )

        leakages = np.empty(
            (offset_end - offset_begin,) + self._leakage_abstract.shape,
            self._leakage_abstract.dtype,
        )
        values = np.empty(
            (offset_end - offset_begin,) + self._value_abstract.shape,
            self._value_abstract.dtype,
        )

        try:

            trace_batch = self.generate_trace_batch(offset_begin, offset_end)

            leakages = self.apply_both_leakage(trace_batch.leakages)
            values = self.apply_both_value(trace_batch.values)

            return TraceBatchContainer(leakages, values)

        except:
            pass

        for i, j in enumerate(range(offset_begin, offset_end)):
            leakage, value = self.generate_trace(j)
            leakages[i] = self.apply_both_leakage(
                leakage.reshape((1,) + leakage.shape)
            )[0]
            values[i] = self.apply_both_value(value.reshape((1,) + value.shape))[0]

        return TraceBatchContainer(leakages, values)


class TraceBatchContainer(Container):
    def __init__(self, *args, **kwargs):

        if len(args) == 2:
            self.leakages = args[0] if not kwargs.get("copy", 0) else np.copy(args[0])
            self.values = args[1] if not kwargs.get("copy", 0) else np.copy(args[1])

        Container.__init__(self, **kwargs)

    def __getitem__(self, key):
        """
        Trace or TraceBatch getter

        :param key: an int or an iterable
        :return: the Trace or TraceBatch containing the Trace in key
        """
        self.logger.debug("__getitem__ with key %s %s" % (str(key), type(key)))

        if isinstance(key, (int, np.int64)):
            leakage = self.apply_both_leakage(self.leakages[key : key + 1])[0]
            value = self.apply_both_value(self.values[key : key + 1])[0]
            return Trace(leakage, value)

        else:

            leakages = self.apply_both_leakage(self.leakages[key])
            values = self.apply_both_value(self.values[key])

            return TraceBatchContainer(leakages, values)

    def __setitem__(self, key, value):
        self.logger.debug("__setitem__ with key %s to %s", str(key), str(value))

        self.leakages[key] = value.leakage if isinstance(key, int) else value.leakages
        self.values[key] = value.value if isinstance(key, int) else value.values

    def save(self, filename):
        """
        Save the current TraceBatchContainer to a file using np.save

        :param filename:
        :return:
        """
        self.logger.debug("save TraceBatch to  %s" % filename)

        with open(filename, "wb") as f:
            np.savez(f, leakages=self.leakages, values=self.values)

    @staticmethod
    def load(filename):
        """
        Load  a file using np.load and create from it a TraceBatchContainer.

        :param filename:
        :return:
        """
        tmp = np.load(filename)
        return TraceBatchContainer(tmp["leakages"], tmp["values"])

    pass

    def __add__(self, other):
        if isinstance(other, Trace):
            return TraceBatchContainer(
                np.vstack([self.leakages, other.leakage])
                if len(self.leakages.shape) > 1
                else np.hstack([self.leakages, other.leakage]),
                np.vstack([self.values, other.value])
                if len(self.values.shape) > 1
                else np.hstack([self.values, other.value]),
            )

        if isinstance(other, TraceBatchContainer):
            return TraceBatchContainer(
                np.vstack([self.leakages, other.leakages])
                if len(self.leakages.shape) > 1
                else np.hstack([self.leakages, other.leakages]),
                np.vstack([self.values, other.values])
                if len(self.values.shape) > 1
                else np.hstack([self.values, other.values]),
            )

    def __eq__(self, other):
        if not isinstance(other, TraceBatchContainer):
            return Container.__eq__(self, other)
        if len(self) != len(other):
            return False
        return np.all(self.leakages == other.leakages) and np.all(
            self.values == other.values
        )

    def get_leakage_mean_var(self):
        """
        Compute mean/var of the leakage.
        :return: mean/var of the container leakages
        """
        try:
            mean, var = self.leakages.mean(0), self.leakages.var(0)
            return self.apply_both_value(mean), self.apply_both_value(var)

        except:
            return Container.get_leakage_mean_var()

    @staticmethod
    def export(container):
        return container[:]


class AbstractArray:
    """
    Used when your leakage or data cannot be represented as an
    array (most of the time in
    :class:`lascar.container.container.AbstractContainer`)
    It simply emulates a few methods needed by other classes (such as
    :class:`lascar.session.Session`)

    :param shape: the shape of your leakages (or values)
    :param dtype: the dtype of your leakages (or values)
    """

    def __init__(self, shape, dtype):
        self.shape = shape
        self.dtype = dtype

    def update(self, array):
        self.shape = array.shape
        self.dtype = array.dtype

    def zeros(self):
        return np.zeros(self.shape, self.dtype)

    def __str__(self):
        return "[%s, %s]" % (self.shape, self.dtype)


class AcquisitionFromGetters(AbstractContainer):
    """
    An AcquisitionFromGetters is built from 2 object whose role are similar:

    - value_getter which delivers values (for instance a class communicating with the dut)
    - leakage_getter which delivers leakages (for instance an oscilloscope)

    value_getter and leakage_getter must either:
    - be iterable: each iteration returns the leakage or value
    OR
    - implement a .get() method which returns leakage or value

    """

    def __init__(self, number_of_traces, value_getter, leakage_getter, **kargs):

        self.value_getter = value_getter
        self.leakage_getter = leakage_getter

        if hasattr(value_getter, "__iter__"):
            self.get_value = lambda: next(self.value_getter)
        elif hasattr(value_getter, "get"):
            self.get_value = lambda: self.value_getter.get()
        else:
            raise ValueError(
                "value_getter must either be an iterator/generator OR implement a get() method"
            )

        if hasattr(leakage_getter, "__iter__"):
            self.get_value = lambda: next(self.leakage_getter)
        elif hasattr(leakage_getter, "get"):
            self.get_leakage = lambda: self.leakage_getter.get()
        else:
            raise ValueError(
                "leakage_getter must either be an iterator/generator OR implement a get() method"
            )

        AbstractContainer.__init__(self, number_of_traces, **kargs)
        self.logger.info("Creating AcquisitionFromGenerators.")

    def generate_trace(self, idx):
        self.logger.debug("Generate trace %d." % (idx))
        value = self.get_value()
        leakage = self.get_leakage()

        return Trace(leakage, value)
