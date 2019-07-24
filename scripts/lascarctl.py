#!/usr/bin/env python3

import click
import importlib
import sys
import time
import itertools
import matplotlib.pyplot as plt
from lascar import *


def load_container(*names):
    """
    Returns a MultipleContainer after creating HdfContainers from *names
    """
    return MultipleContainer( *[Hdf5Container(i) for i in names])

def import_object_from_module( module_name, object_name):
    """
    equivalent of "from module_name import object_name"
    (dirty...)
    """
    sys.path.append( '/'.join( module_name.split('/')[:-1])  )
    module =  importlib.import_module(module_name.split('/')[-1].replace('.py',''))
    sys.path.remove( '/'.join( module_name.split('/')[:-1])  )
    return getattr(module , object_name)

def dumb_generator():
    i = 0
    while True:
        yield i*np.ones((4,))
        i+=1

def browse_container(container, wait=0, plot=None):
    for i,leakage_value in enumerate(container):
        leakage, value =leakage_value 
        print(i,value)
        if plot:
            plt.plot(leakage)
        time.sleep(wait)
    if plot:
        plt.show()

@click.group()
def main():
    """lascarctl.

    lascar scripting commands.
    """
    pass

@main.command()
@click.option("-n", "--number_of_traces", default=10, type=int, help="indicate the number of traces you wish to acquire")
@click.option("-v","--value_generator", nargs=2, default=[__file__, "dumb_generator"], help="indicate value_generator module_name and object_name")
@click.option("-l","--leakage_generator", nargs=2, default=[__file__, "dumb_generator"], help="indicate leakage_generator module_name and object_name")
@click.option("-o", "--output", type=str, default=None, help="indicate the name for the output file (hdf5 for now).")
@click.option("-b", "--batch_size", default=100, type=int,help='set the batch_size for lascar session')
@click.option("-w", "--wait", default=0,type=float, help='delay in sec between trace requests')
@click.option("-p", "--plot", is_flag=True,help="boolean to plot traces with matplotlib during acquisition")
def acquisition( number_of_traces, value_generator, leakage_generator, output, batch_size, wait, plot):
    """
    Acquire side-channel data.

    Must input number_of_traces and two generators: one leakage_generator, one value_generator

    """
    value_generator = import_object_from_module(*value_generator)
    leakage_generator = import_object_from_module(*leakage_generator)
    
    acquisition_container = AcquisitionFromGenerators(number_of_traces, value_generator(), leakage_generator())

    if output:
        Hdf5Container.export(acquisition_container, output, batch_size=batch_size, name=output.split('/')[-1])
    else:
        browse_container(acquisition_container, wait, plot)


@main.command()
@click.argument("name_in", nargs=-1)
@click.option("-o", "--name_out", default=None, help="indicate the name for the output file (hdf5 for now).")
@click.option("-l", "--leakage_processing", nargs=2, default=None, help="indicate leakage_processing module_name and object_name")
@click.option("-v", "--value_processing", nargs=2, default=None, help="indicate value_processing module_name and object_name")
@click.option("-b", "--batch_size", default=100, type=int,help='set the batch_size for lascar session')
@click.option("-p", "--plot", is_flag=True,help="boolean to plot traces while acquisition")
@click.option("-n", "--number_of_traces", default=0, type=int, help="indicate the number of traces you wish to process")
def processing(name_in, name_out, leakage_processing, value_processing, batch_size, plot, number_of_traces):
    """
    Process (modify) a container, and output to a new one.
    (ie apply a function on leakages and/or values of the container)
    
    - names_in : names of the container you want to process

    """
    leakage_processing = import_object_from_module(*leakage_processing) if leakage_processing else None
    value_processing = import_object_from_module(*value_processing) if value_processing else None
    
    container = load_container(*name_in)

    if number_of_traces:
        container.number_of_traces = number_of_traces

    container.leakage_processing = leakage_processing
    container.value_processing = value_processing

    if name_out:
        Hdf5Container.export(container, name_out, batch_size=10, name=name_out.split('/')[-1])
    else:
        browse_container(container,plot=plot)


@main.command()
@click.argument("name_in", nargs=-1)
@click.argument("module",type=str)
@click.option("-e","--engines", default="engines", help="specify engines name within module")
@click.option("-o","--output_method", default="output_method",  help="specify output_method name within module")
@click.option("-b", "--batch_size", default=100, type=int,help='set the batch_size for lascar session')
@click.option("-n", "--number_of_traces", default=0, type=int, help="indicate the number of traces you wish to use ")
def run(name_in, module, engines, output_method, batch_size, number_of_traces):
    """
    Run a lascar session on a container.
    
    Must specify:
    - name_in : the name of the container file (hdf5 for now)
    - module : path to a python module containing engines/output_method definition
    """    
    container = load_container(*name_in)

    if number_of_traces:
        container.number_of_traces = number_of_traces

    engines = import_object_from_module(module , engines)
    output_method = import_object_from_module(module , output_method)

    session = Session(container, engines=engines, output_method=output_method).run(batch_size)


@main.command()
@click.argument("names_in", nargs=-1)
@click.option("-b", "--batch_size", default=100, type=int, help='set the batch_size for lascar session')
@click.option("-o","--name_out", default=None, help="npy.save the ttests to name_out")
@click.option("-p", "--plot", is_flag=True,help="plot the computed ttests with matplotlib")
def ttest(names_in, batch_size, name_out, plot):
    """
    Compute Welch-ttest on containers.

    Each set of trace represent a different class for the ttest.
    (no partitioning done)

    For each pair of set of trace, a ttest is computed.

    """

    containers = [Hdf5Container(i) for i in names_in]
    results = compute_ttest(*containers, batch_size=batch_size)

    if plot:
        labels = [i.split('/')[-1] for i in names_in]
        for e,ij in enumerate(itertools.combinations(range(len(containers)),2)):
            i,j = ij
            plt.plot(results[e], label="%s versus %s"%(labels[i], labels[j]))            
            plt.xlabel("Time samples")
            plt.ylabel("ttest")
        plt.legend()
        plt.show()

    if name_out:
        np.save(name_out, results)

@main.command()
@click.argument("names_in", nargs=-1)
@click.option("-l", "--leakages_dataset", default="leakages", type=str, help='Indicate the name of the leakage dataset')
@click.option("-v", "--values_dataset", default="values", type=str, help='Indicate the name of the values dataset')
def info(names_in, leakages_dataset, values_dataset):
    """
    Get information on an Hdf5Container
    """
    container = load_container(*names_in)
    print(container)



from PyQt5 import QtWidgets as qt
import PyQt5.QtCore as qtc
import numpy as np
from vispy import scene, color

import pkg_resources

import numpy as np
from vispy import scene
from vispy import color



class plot:

    bg_clr = "#222"  # dark background color
    # bg_clr = "#fff"  # clear
    highlighted = color.Color("#41CCB4")
    others = highlighted.darker(0.5)

    def __init__(self, parent=None):
        self.canvas = scene.SceneCanvas(
            size=(1280, 900),
            keys="interactive",
            bgcolor=plot.bg_clr,
            parent=parent,
        )

        self.grid = self.canvas.central_widget.add_grid(spacing=0)
        self.view = self.grid.add_view(row=0, col=1, camera="panzoom")
        self.colormap = color.get_colormap('husl')[np.linspace(0., 1., 24)]

        self.n = 0
        self.lines = {}

        self.x_axis = scene.AxisWidget(orientation="bottom", text_color="#ddd")
        self.y_axis = scene.AxisWidget(orientation="left", text_color="#ddd")
        self.x_axis.stretch = (1, 0.05)
        self.y_axis.stretch = (0.05, 1)
        self.grid.add_widget(self.x_axis, row=1, col=1)
        self.grid.add_widget(self.y_axis, row=0, col=0)
        self.x_axis.link_view(self.view)
        self.y_axis.link_view(self.view)

        self.canvas.show()
        if parent is None:
            self.canvas.app.run()

    def add_curve(self, curve, index):
        self.n += 1
        self.lines[index] = scene.LinePlot(curve, color=self.colormap[self.n], parent=self.view.scene)
        # self.view.camera.set_range(x=(0, curve.shape[0]), y=(curve.min(), curve.max()))

    def remove_curve(self, index):
        self.n -= 1
        self.lines[index].parent = None
        self.lines[index] = None
        self.lines.pop(index)


class CurveSelector(qt.QMainWindow):
    def __init__(self, c):

        super().__init__()

        style_file = pkg_resources.resource_filename(__name__, "/styles.css")

        #with open(style_file) as stylesheet:
        #    self.setStyleSheet(stylesheet.read())

        self.etraces = c.leakages
        self.instr = [ str(i) for i in range(len(c))]
        self.index = 0
        self.current_selection = []
        self.add_widgets()
        self.place_widgets()

    def add_widgets(self):
        self.plot_ = plot(parent=self)
        self.plot_.view.camera.set_range(x=(0, self.etraces.shape[1]), y=(self.etraces[0].min(), self.etraces[0].max()))
        self.instr_list = qt.QListWidget(self)
        self.instr_list.setSelectionMode(3)
        self.instr_list.currentRowChanged.connect(self.rowchange)
        self.instr_list.addItems(self.instr)

    def rowchange(self, event):
        s = list(map(self.instr_list.row,self.instr_list.selectedItems()))
        r = set(self.current_selection)
        delete_items = r-set(s)
        add_items = set(s)-r

        for i in delete_items:
            self.plot_.remove_curve(i)

        for i in add_items:
            self.plot_.add_curve(self.etraces[i],i)

        self.current_selection = s

        # self.instr_change_focus(self.instr_list.currentItem())

    def instr_change_focus(self, item):
        self.index = self.instr_list.row(item)
        self.focus_change(self.index)

    def focus_change(self, r):
        self.plot_.line.set_data(self.etraces[r], symbol=None)

    def place_widgets(self):
        self.frame = qt.QFrame(self)
        self.setCentralWidget(self.frame)

        self.frame_layout = qt.QHBoxLayout(self.frame)
        self.frame_layout.addWidget(self.instr_list)
        self.frame_layout.addWidget(self.plot_.canvas.native)

    @main.command()
    @click.argument("name_in")
    def plot(name_in):
        """
        Plot an Hdf5Container
        """
        container = Hdf5Container(name_in)
        app_ = qt.QApplication([])

        v = CurveSelector( container)
        v.show()
        sys.exit(app_.exec_())


if __name__ == "__main__":
    main()

