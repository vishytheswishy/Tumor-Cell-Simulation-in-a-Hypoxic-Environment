"""
Activator cells, consumer cells, and neutral cells.

If an activator cell is active, it will activate both consumers and activators
in the vicinity by transferring oxygen to each. If a consumer cell is active,
it will eventually start sending a negative oxygen to its neighbors.

Activation occurs when oxygen > 10. Once activated, the cell has a chance of
deactivation that increases with activation duration.
"""

import random as r
import math
from mesa import Agent
from mesa.model import Model
from mesa.space import SingleGrid
from mesa.time  import BaseScheduler, SimultaneousActivation
import random
import matplotlib.pyplot as plt


import sim_settings as ss

fig,ax = plt.subplots(1,1)
ax.set_xlabel('X') ; ax.set_ylabel('Y')
ax.set_xlim(0,360) ; ax.set_ylim(-1,1)
xs, ys = [], []
Cell_Dict = {'cancer':0,'n':0, 'capillary':0}
step_cancer = list()
step_capillary = list()
step_n = list()
oxy_num = 0

def count_cell_type(cell_list, cell_type):
    count = 0
    for t in cell_list:
        if type(t).__name__ == cell_type:
            count += 1
    return count


class Cell(Agent):
    """
    Base Cell class.
    """

    def __init__(self, unique_id, model, activated = False, activation_odds = 0.5):
        super().__init__(unique_id, model)
        self.oxygen = 0
        self.activated = activated
        self.vegf = 0
        self.steps = 0

    def step_maintenance(self):
        oxy_num = self.steps
        self.steps += 1
        self.subtract_oxygen(ss.CELL_OXYGEN_CONSUMPTION)
        targets = list(self.model.grid.neighbor_iter(self.pos, moore = True))

        targets.sort(key=lambda x: x.oxygen)
        # the logic here need work
        # how do we decide the oxygen distribution
        # do we look at all neighbors?

        # can move in all directions
        # probability based on differences and diffusion constant
        # oxygen packets can move in any direction
        for t in targets:
            if type(t).__name__ != "Capillary":
                oxy_to_add = abs((self.oxygen - t.oxygen)/3)
                if self.oxygen > oxy_to_add and self.oxygen > t.oxygen:
                    self.subtract_oxygen(oxy_to_add)
                    t.add_oxygen(oxy_to_add)

        targets.sort(key=lambda x: x.vegf)
        for t in targets:
            vegf_to_add = (self.vegf - t.vegf)/2
            if vegf_to_add > 0:
                self.vegf -= vegf_to_add
                t.vegf += vegf_to_add

        if self.steps > ss.CELL_DEACTIVATION_MIN_STEPS and self.oxygen < 10:
            self.roll_for_deactivation()


    # rolls for a chance for the cell to become empty cell
    def roll_for_deactivation(self):
        if type(self).__name__ != "Empty":
            roll = roll = r.random()

            # decreasing odds of survival at lower oxygen levels
            if roll > 0.4 + (self.oxygen)* 0.1:
                new_empty_agent = Empty(self.pos, self.model)
                coord = self.pos
                print(coord)
                self.model.grid.remove_agent(self)
                self.model.grid.scheduler.remove(self)

                self.model.grid.place_agent(new_empty_agent, coord)
                self.model.grid.scheduler.add(new_empty_agent)
                print(type(self).__name__, " cell died at" , coord)

    def step(self):
        self.step_maintenance()


    def add_oxygen(self, n):
        if self.oxygen + n < ss.MAX_OXYGEN_CAPACITY:
            self.oxygen += n
        else:
            self.oxygen = ss.MAX_OXYGEN_CAPACITY

    def subtract_oxygen(self, n):
        if self.oxygen - n >= 0:
            self.oxygen -= n
        else:
            self.oxygen = 0


class Capillary(Cell):
    """
    Cell that provides oxygen and nutritions to neighboring cells

    There is a chance that the capillary will expand into a neighboring cell
    if the cell is empty and the amount of VEGF marker is above a certain threshold
    """

    def __init__(self, unique_id, model, activated = True, supply = ss.MAX_OXYGEN_CAPACITY):
        super().__init__(unique_id, model, activated)
        self.supply = supply


    def step(self):
        # self.step_maintenance()
        # send activation oxygen to the neighboring cells if activated
        if self.activated:
            targets = list(self.model.grid.neighbor_iter(self.pos, moore = True))

            for t in targets:
                if type(t).__name__ != "Capillary":
                    t.add_oxygen(self.supply)

                t_neighs = list(self.model.grid.neighbor_iter(t.pos, moore = True))
                neighboring_caps = count_cell_type(t_neighs, "Capillary")
                # limit blood vessel growth
                # feedback system to limit the growth
                # smaller capillary, less oxygen supply
                # consume vegf
                if neighboring_caps < ss.CAPILLARY_GROWTH_DENSITY_LIMIT and t.vegf > 10 and type(t).__name__ == "Empty" and self.supply > 20:
                    roll = r.random()
                    if roll < 0.1:
                        neighboring_caps += 1
                        t.vegf = 0
                        for t_neigh in t_neighs:
                            t_neigh.vegf = 0
                        coord = t.pos
                        self.model.grid.remove_agent(t)
                        self.model.grid.scheduler.remove(t)
                        new_cap = Capillary(coord, self.model, supply=ss.CAPILLARY_GROWTH_FRACTION*self.supply)
                        Cell_Dict['capillary'] = Cell_Dict.get('capillary') + 1
                        self.model.grid.place_agent(new_cap, coord)
                        self.model.grid.scheduler.add(new_cap)

                
        self.oxygen = self.supply
        # self.step_maintenance()


class Cancer(Cell):
    """
        Cancer cell that consumes oxygen to produce itself.
        If there is enough nutrition, the cell will duplicate into a random neighboring cell while consuming half of its energy
        There is also a little chance for the cancer cell to produce VEGF if it is oxygen deficient
            - Vascular endothelial growth factor (VEGF) is a signalling protein that promotes the growth of new blood vessels.
    """
    def __init__(self, unique_id, model, activated = True, vegf_mutation = False):
        super().__init__(unique_id, model, activated)
        self.vegf_mutation = vegf_mutation


    def step(self):
        # self.step_maintenance()
        self.subtract_oxygen(10)

        if self.oxygen < ss.CANCER_OXYGEN_VEGF_LIMIT:
            self.roll_for_vgef()

        targets = self.model.grid.neighbor_iter(self.pos, moore = True)
        for t in targets:
            roll = r.random()
            if self.oxygen > ss.CANCER_OXYGEN_DUPLICATION_LIMIT and type(t).__name__ == "Empty" and roll < ss.CANCER_DUPLICATION_CHANCE:
                self.subtract_oxygen(ss.CANCER_DUPLICATION_OXYGEN_COST)
                coord = t.pos
                self.model.grid.remove_agent(t)
                self.model.grid.scheduler.remove(t)
                new_cancer = Cancer(coord, self.model, vegf_mutation=self.vegf_mutation)
                Cell_Dict['cancer'] = Cell_Dict.get('cancer') + 1 
                self.model.grid.place_agent(new_cancer, coord)
                # when replacing an empty cell, make sure to add it to the scheduler
                self.model.grid.scheduler.add(new_cancer)

        # there is chance to mutate and produce vegf


        if self.vegf_mutation:
            self.vegf = ss.CANCER_VEGF_SUPPLY

        # to propogate unused resources to other cells
        self.step_maintenance()

        if self.vegf_mutation:
            self.vegf = ss.CANCER_VEGF_SUPPLY
        # tumor necrosis
        # remove tumor cells in the middle of cluster

        # wont kill the intial one
        # kill after some


    def roll_for_vgef(self):
        roll = r.random()
        if roll < ss.CANCER_VEGF_CHANCE:
            self.vegf_mutation = True

class Normal(Cell):
    """
    Cell consumes some oxygen and send the remaining to other cells
    """
    def step(self):
        self.subtract_oxygen(ss.NORMAL_OXYGEN_CONSUMPTION)
        self.step_maintenance()


class Empty(Cell):
    """
    Cell that can be replaced
    """

    def step(self):
        if self.pos == None:
            return
        self.step_maintenance()



class PetriDish(Model):
    """
    Main model instance. It assignes one cell in each grid location, selecting
    its type randomly at the time of assignment; it assigns a single activated
    Producer cell in the middle of the grid.
    """

    def __init__(self, width = 20, height = 20, proportion_normal = 0.3):
        self.running = True
        self.schedule = SimultaneousActivation(self)
        self.grid = SingleGrid(width, height, torus = False)

        self.grid.scheduler = self.schedule

        cancer_x = random.randint(width//4, width - 1)
        while True:
            cancer_y = cancer_x + random.randint(-5, 5)
            if cancer_y >= 0 and cancer_y < height and cancer_y != cancer_x:
                break

        cancer_coords = (cancer_x, cancer_y)

        ## Rolled into the placement of other cells
        # self.schedule.add(initial_activator)
        # self.grid.place_agent(initial_activator, center_coords)

        # roll a die and place Producer, Consumer or undifferentiated cell
        for x in range(width):
            for y in range(height):
                roll = r.random()
                coords = (x, y)
                if coords[0] == width - 1:
                    Cell_Dict['capillary'] = Cell_Dict.get('capillary') + 1
                    agent = Capillary(coords, self)
                elif coords == cancer_coords:
                    agent = Cancer(coords, self)
                    Cell_Dict['cancer'] = Cell_Dict.get('cancer') + 1
                elif roll <= proportion_normal:
                    agent = Normal(coords, self)
                    Cell_Dict['n'] = Cell_Dict.get('n') + 1
                else:
                    agent = Empty(coords, self)

                self.schedule.add(agent)
                self.grid.place_agent(agent, coords)


    # random permuation each time.
    # shuffle
    def step(self):
        # self.schedule = shuffle(self.schedule)
        steps = self.schedule.steps
        print(steps)
        print(Cell_Dict)
        with open("data.txt", "a") as file_object:
            # Append 'hello' at the end of file
            file_object.write(str(steps)+ " " + str(Cell_Dict['cancer']) + " " +  str(Cell_Dict['capillary']) + "\n")
        # plt.scatter
        # plt.show()
        # plt_dynamic(steps, Cell_Dict['cancer'], ax , 'red')
        self.schedule.step() # goes through agents in the order of addition

def plt_dynamic(x, y, ax, colors=['b']):
    for color in colors:
        ax.scatter(x, y, color)
    fig.canvas.draw()
    
