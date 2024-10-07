import pygame as pg
import asyncio
import numpy as np
from math import floor, ceil
import cv2
from enum import Enum
import time

from game import GameOfLife


if __name__ == '__main__':
    vec = pg.Vector2
    # This is the program entry point
    pg.init()

    game_of_life = GameOfLife(cells=200)

    game_of_life.addPattern("oscillators", "toad", vec(13, 0))
    game_of_life.addPattern("spaceships", "glider", vec(2, 3))
    game_of_life.addPattern("spaceships", "glider", vec(6, 4))
    game_of_life.addPattern("oscillators", "pulsar", vec(11, 16))
    game_of_life.addPattern("oscillators", "pulsar", vec(26, 20))

    game_of_life.addPattern("oscillators", "beacon", vec(10, 11))
    game_of_life.addPattern("spaceships", "spaceship_l", vec(4, 10))
    game_of_life.addPattern("starters", "acorn", vec(120, 120))

    asyncio.run(game_of_life.run())