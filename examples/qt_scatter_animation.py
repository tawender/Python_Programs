import numpy as np
from PyQt4 import QtGui
import sys
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

class mplWidget(FigureCanvasQTAgg):
    def __init__(self):
        super(mplWidget, self).__init__(mpl.figure.Figure(figsize=(7, 7)))

        self.setupAnim()
        self.show()

    def setupAnim(self):
        ax = self.figure.add_axes([0, 0, 1, 1], frameon=False)
        ax.axis([0, 1, 0, 1])
        ax.axis('off')

        # Create rain data
        self.n_drops = 50
        self.rain_drops = np.zeros(self.n_drops, dtype=[('position', float, 2),
                                                        ('size',     float, 1),
                                                        ('growth',   float, 1),
                                                        ('color',    float, 4)
                                                        ])

        # Initialize the raindrops in random positions and with
        # random growth rates.
        self.rain_drops['position'] = np.random.uniform(0, 1, (self.n_drops, 2))
        self.rain_drops['growth'] = np.random.uniform(50, 200, self.n_drops)

        # Construct the scatter which we will update during animation
        # as the raindrops develop.
        self.scat = ax.scatter(self.rain_drops['position'][:, 0],
                               self.rain_drops['position'][:, 1],
                               s=self.rain_drops['size'],
                               lw=0.5, facecolors='none',
                               edgecolors=self.rain_drops['color'])

        self.animation = FuncAnimation(self.figure, self.update_plot,
                                       interval=10, blit=True)

    def update_plot(self, frame_number):
        # Get an index which we can use to re-spawn the oldest raindrop.
        indx = frame_number % self.n_drops

        # Make all colors more transparent as time progresses.
        self.rain_drops['color'][:, 3] -= 1./len(self.rain_drops)
        self.rain_drops['color'][:, 3] = np.clip(self.rain_drops['color'][:, 3], 0, 1)

        # Make all circles bigger.
        self.rain_drops['size'] += self.rain_drops['growth']

        # Pick a new position for oldest rain drop, resetting its size,
        # color and growth factor.
        self.rain_drops['position'][indx] = np.random.uniform(0, 1, 2)
        self.rain_drops['size'][indx] = 5
        self.rain_drops['color'][indx] = (0, 0, 0, 1)
        self.rain_drops['growth'][indx] = np.random.uniform(50, 200)

        # Update the scatter collection, with the new colors,
        # sizes and positions.
        self.scat.set_edgecolors(self.rain_drops['color'])
        self.scat.set_sizes(self.rain_drops['size'])
        self.scat.set_offsets(self.rain_drops['position'])

        return self.scat,


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = mplWidget()
    sys.exit(app.exec_())