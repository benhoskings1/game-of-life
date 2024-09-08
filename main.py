import numpy as np
import pygame as pg
import pandas as pd
from math import floor, ceil
import cv2
from enum import Enum
import time

from Patterns.Still_Lifes import *
from Patterns.Oscillators import *
from Patterns.Spaceships import *

vec = pg.Vector2


patterns = {"Block": block, "BeeHive": beeHive, "Loaf": loaf,
            "Blinker": blinker, "Toad": toad, "Beacon": beacon, "Pulsar": pulsar,
            "Glider": glider, "Spaceship L": spaceshipLight, "Spaceship M": spaceshipMiddle,
            "Spaceship H": spaceshipHeavy}


class GameOfLife:
    def __init__(self, cells=60):
        self.display = pg.display.set_mode((800, 800))
        self.baseSurf = pg.Surface((800, 800))
        self.baseSurf.fill([255, 255, 255])
        self.display.fill([255, 255, 255])
        self.gridSize = vec(cells, cells)
        self.grid = np.zeros([cells, cells])

        self.kernel = np.ones([3, 3])
        self.kernel[1, 1] = 0

        self.running = True

        self.iteration = 0

        self.fps = 1000

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

    def render(self):
        newSurf = self.baseSurf.copy()
        cellSurf = pg.Surface(self.baseSurf.get_size(), pg.SRCALPHA)

        boarderWidth = 0
        cellSize = (vec(newSurf.get_size()) - vec([(boarderWidth *
                                                    (self.gridSize.x + 1)) for i in range(2)])) / self.gridSize.x

        cellSize = vec(floor(cellSize.x), floor(cellSize.y))

        for rowIdx, row in enumerate(self.grid):
            for colIdx, cell in enumerate(row):
                if cell:
                    rect = pg.Rect([colIdx * cellSize.y, rowIdx * cellSize.x], cellSize)
                    pg.draw.rect(cellSurf, [0, 0, 0], rect)

        newSurf.blit(cellSurf, [0, 0])
        self.display.blit(newSurf, [0, 0])
        pg.display.set_caption(str.format("Iteration: {}", self.iteration))
        pg.display.flip()

    def run(self):
        auto = False
        start = time.monotonic()
        while self.running:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_RIGHT:
                        keyup = False
                        self.update()
                        self.render()
                        start = time.monotonic()

                        while not keyup:
                            for event in pg.event.get():
                                if event.type == pg.KEYUP:
                                    keyup = True

                            if time.monotonic() - start >= (1 / self.fps):
                                start = time.monotonic()
                                self.update()
                                self.render()

                    if event.key == pg.K_SPACE:
                        auto = not auto
                        start = time.monotonic()

            if auto:
                if time.monotonic() - start >= (1 / self.fps):
                    start = time.monotonic()
                    self.update()
                    self.render()

            self.render()


pg.init()
pg.event.pump()
game = GameOfLife()
game.addPattern("Toad", vec(8, 0))
game.addPattern("Glider", vec(2, 3))
game.addPattern("Glider", vec(7, 3))
game.addPattern("Pulsar", vec(30, 20))
game.addPattern("Spaceship H", vec(4, 10))
game.addPattern("Beacon", vec(20, 25))
game.run()