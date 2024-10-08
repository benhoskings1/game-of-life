import numpy as np

glider = np.array([
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1]
])

spaceshipLight = np.array([
    [0, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0]
])

spaceshipMiddle = np.array([
    [0, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 0]
])

spaceshipHeavy = np.array([
    [0, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 1, 0],
])