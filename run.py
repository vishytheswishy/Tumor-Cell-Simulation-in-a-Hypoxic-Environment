from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from server import server
import os

server.port = int(os.environ.get("PORT", 5000))
server.launch()
