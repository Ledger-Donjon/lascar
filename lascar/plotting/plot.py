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

import numpy as np
from vispy import scene
from vispy import color

# Starting from https://gist.github.com/yhql/70c3e59019cb73ec83870e946166b95f

bg_clr = '#222' # dark background color

class plot:
    """
    Fast plot of many large traces as a single object, using vispy. 
    """

    def __init__(self, icurves, highlight=None, clrmap='husl', colors=None):
        """ 
        :param icurves: input curve or list of curves
        :param clrmap: (optional) what colormap name from vispy.colormap to use
        :param highlight: (optional) index of a curve to highlight 
        :param colors: (optional) use list of colors instead of colormap
        """ 
        self.canvas = scene.SceneCanvas(size=(1280, 900), position=(200, 200), keys='interactive', bgcolor=bg_clr)

        self.grid = self.canvas.central_widget.add_grid(spacing=0)
        self.view = self.grid.add_view(row=0, col=1, camera='panzoom')

        curves = np.array(icurves)
        if len(curves.shape) == 1:
            ## Single curve
            curves = np.array([icurves])

        nb_traces, size = curves.shape

        # the Line visual requires a vector of X,Y coordinates 
        xy_curves = np.dstack((np.tile(np.arange(size), (nb_traces, 1)), curves))

        # Specify which points are connected
        # Start by connecting each point to its successor
        connect = np.empty((nb_traces * size - 1, 2), np.int32)
        connect[:, 0] = np.arange(nb_traces * size - 1)
        connect[:, 1] = connect[:, 0] + 1

        # Prevent vispy from drawing a line between the last point 
        # of a curve and the first point of the next curve 
        for i in range(size, nb_traces * size, size):
            connect[i - 1, 1] = i - 1
        if highlight is not None:
            # 'husl' is horrible in this case so we switch to viridis
            colormap = color.get_colormap('viridis')[np.linspace(0., 1., nb_traces * size)]
            # cheat by predrawing a single line over the highlighted one
            scene.Line(pos=xy_curves[highlight], color=colormap[connect.shape[0]-1][0], parent=self.view.scene)
            scene.Line(pos=xy_curves, color=colormap[connect.shape[0]//2][0], parent=self.view.scene, connect=connect)
        else:
            if colors is None:
                colormap = color.get_colormap(clrmap)[np.linspace(0., 1., nb_traces * size)]
            else:
                colormap = color.get_colormap(clrmap)[colors]
            scene.Line(pos=xy_curves, color=colormap, parent=self.view.scene, connect=connect)

        self.x_axis = scene.AxisWidget(orientation='bottom')
        self.y_axis = scene.AxisWidget(orientation='left')
        self.x_axis.stretch = (1, 0.05)
        self.y_axis.stretch = (0.05, 1)
        self.grid.add_widget(self.x_axis, row=1, col=1)
        self.grid.add_widget(self.y_axis, row=0, col=0)
        self.x_axis.link_view(self.view)
        self.y_axis.link_view(self.view)

        self.view.camera.set_range(x=(-1, size), y=(curves.min(), curves.max()))

        self.canvas.show()
        self.canvas.app.run()

if __name__ == "__main__":
    a = np.random.normal(0., 500, (20, 20_000))
    plot(a, highlight=3)
    plot(a)