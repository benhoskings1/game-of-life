import numpy as np
import pygame as pg
import pandas as pd
from math import floor, ceil
import cv2
from enum import Enum
import time

from screen import Screen, Colours
from game_screen import TouchScreen, GameButton, GameObjects

from Patterns.Still_Lifes import *
from Patterns.Oscillators import *
from Patterns.Spaceships import *

vec = pg.Vector2


patterns = {"Block": block, "BeeHive": beeHive, "Loaf": loaf,
            "Blinker": blinker, "Toad": toad, "Beacon": beacon, "Pulsar": pulsar,
            "Glider": glider, "Spaceship L": spaceshipLight, "Spaceship M": spaceshipMiddle,
            "Spaceship H": spaceshipHeavy}


class GameOfLife:
    def __init__(self, cells=60, frameless=False):

        self.display_size = vec(800, 800)
        self.touch_size = vec(200, 800)

        # Setting up the game graphics
        if frameless:
            flags = pg.NOFRAME | pg.SRCALPHA
        else:
            flags = pg.SRCALPHA

        self.window = pg.display.set_mode((self.display_size.x + self.touch_size.x,
                                           self.display_size.y),
                                          flags)

        self.left_screen = self.window.subsurface(((0, 0), self.display_size))
        self.right_screen = self.window.subsurface((self.display_size.x, 0), self.touch_size)

        self.display_screen = Screen(self.display_size, colour=Colours.white)
        self.touch_screen = TouchScreen(self.touch_size, colour=Colours.midGrey)

        self.reset_button = GameButton((10, 10), pg.Vector2(120, 50),
                                       id=1, text="Restart", colour=Colours.red)

        self.touch_screen.sprites = GameObjects([self.reset_button])

        self.gridSize = vec(cells, cells)
        self.grid = np.zeros([cells, cells])

        self.grid_init = np.zeros([cells, cells])

        self.kernel = np.ones([3, 3])
        self.kernel[1, 1] = 0

        self.running = True

        self.iteration = 0

        self.fps = 1000

        self.update_display()

    def update_display(self, display_screen=None, touch_screen=None):
        if display_screen is None:
            display_screen = self.display_screen
        if touch_screen is None:
            touch_screen = self.touch_screen

        self.left_screen.blit(display_screen.get_surface(), (0, 0))
        self.right_screen.blit(touch_screen.get_surface(), (0, 0))

        pg.display.set_caption(str.format("Iteration: {}", self.iteration))
        pg.display.flip()


    def addPattern(self, name, position: vec):
        pattern: np.ndarray = patterns[name]
        self.grid[int(position.y): int(position.y) + pattern.shape[0],
                  int(position.x): int(position.x) + pattern.shape[1]] = pattern

    def update(self):
        neighbours = cv2.filter2D(self.grid, -1, self.kernel, borderType=cv2.BORDER_CONSTANT)

        newGrid = np.zeros(self.grid.shape)

        newGrid[np.logical_and(neighbours == 3, self.grid == 0)] = 1
        newGrid[np.logical_and(np.logical_or(neighbours == 2, neighbours == 3), self.grid == 1)] = 1

        self.grid = newGrid
        self.iteration += 1

    def load_update(self):
        # TODO: create logical difference between new and previous grid
        self.display_screen.refresh()

        newSurf = self.display_screen.surface.copy()
        cellSurf = pg.Surface(self.display_size, pg.SRCALPHA)

        boarderWidth = 0
        cellSize = (vec(newSurf.get_size()) - vec([(boarderWidth *
                                                    (self.gridSize.x + 1)) for i in range(2)])) / self.gridSize.x

        cellSize = vec(floor(cellSize.x), floor(cellSize.y))

        for rowIdx, row in enumerate(self.grid):
            for colIdx, cell in enumerate(row):
                if cell:
                    rect = pg.Rect([colIdx * cellSize.y, rowIdx * cellSize.x], cellSize)
                    pg.draw.rect(cellSurf, [0, 0, 0], rect)

        self.display_screen.surface.blit(cellSurf, (0, 0))

    def process_iteration(self):
        self.update()
        self.load_update()
        self.update_display()

    def get_relative_mose_pos(self):
        return pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(self.display_size.y, 0)

    def run(self):
        self.load_update()
        self.update_display()

        self.grid_init = self.grid

        auto = False
        start = time.monotonic()
        while self.running:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.MOUSEBUTTONDOWN:
                    button_id = self.touch_screen.click_test(self.get_relative_mose_pos())
                    if button_id:
                        if button_id == 1:
                            self.grid = self.grid_init
                            self.iteration = 0
                            self.load_update()
                            self.update_display()

                        print(button_id)

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_RIGHT:
                        keyup = False
                        start = time.monotonic()

                        while not keyup:
                            for event in pg.event.get():
                                if event.type == pg.KEYUP:
                                    keyup = True

                            if time.monotonic() - start >= (1 / self.fps):
                                start = time.monotonic()
                                self.process_iteration()

                    if event.key == pg.K_SPACE:
                        auto = not auto
                        start = time.monotonic()

            if auto:
                if time.monotonic() - start >= (1 / self.fps):
                    start = time.monotonic()
                    self.process_iteration()

            # self.render()


if __name__ == "__main__":
    pg.init()

    game = GameOfLife()

    game.addPattern("Toad", vec(8, 0))
    game.addPattern("Glider", vec(2, 3))
    game.addPattern("Glider", vec(7, 3))
    game.addPattern("Pulsar", vec(30, 20))
    game.addPattern("Spaceship H", vec(4, 10))
    game.addPattern("Beacon", vec(20, 25))

    game.run()
