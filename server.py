from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import cell as c
import numpy as np


from mesa.visualization.ModularVisualization import VisualizationElement

class HistogramModule(VisualizationElement):
    package_includes = ["Chart.min.js"]
    local_includes = ["HistogramModule.js"]

    def __init__(self, bins, canvas_height, canvas_width):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        new_element = "new HistogramModule({}, {}, {})"
        new_element = new_element.format(bins,
                                         canvas_width,
                                         canvas_height)
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        wealth_vals = [agent.oxygen for agent in model.schedule.agents]
        hist = np.histogram(wealth_vals, bins=self.bins)[0]
        return [int(x) for x in hist]


def cell_portrayal(cell):
    if type(cell).__name__ == "Capillary":
        cell_color = "red"
    elif type(cell).__name__ == "Normal":
        cell_color = "green"
    elif type(cell).__name__ == "Cancer":
        cell_color = "purple"
    else:
        cell_color = "grey"

    portrayal = {"Shape": "circle",
                 "Color": cell_color,
                 # "Filled": str(cell.activated),
                 "Filled": "false",
                 "Layer": 0,
                 "r": max(0.1, cell.oxygen / 100)}
    return portrayal



def vegf_portrayal(cell):
    if type(cell).__name__ == "Capillary":
        cell_color = "red"
    elif type(cell).__name__ == "Normal":
        cell_color = "green"
    elif type(cell).__name__ == "Cancer":
        cell_color = "purple"
    else:
        cell_color = "grey"

    portrayal = {"Shape": "circle",
                 "Color": cell_color,
                 # "Filled": str(cell.activated),
                 "Filled": "false",
                 "Layer": 0,
                 "r": max(0.1, cell.vegf / 50)}
    return portrayal

width = 20
height = 20

# new state vs old state for the simulation


grid = CanvasGrid(cell_portrayal, width, height, 600, 600)

vegf_grid = CanvasGrid(vegf_portrayal, width, height, 600, 600)

histogram = HistogramModule(list(range(100)), 200, 500)

# todo
# add visualization under the plot
# - total number of cells in each category
# - total concentration of oxygen
# - total oxygen consumption

# - measurements
# historgram of cells
# Record
# latent tumor
# tumor necrosis inside tumor

server = ModularServer(c.PetriDish, [grid, vegf_grid, histogram], "Simple cell activation model",
                       {
                           "width": width, "height": height
                       })
