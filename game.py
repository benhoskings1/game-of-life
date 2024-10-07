import numpy as np
import pygame as pg
from math import floor, ceil
import cv2
from enum import Enum
import time

import asyncio

from screen import Screen, Colours, BlitLocation
from game_screen import TouchScreen, GameButton, GameObjects

from Patterns.Still_Lifes import *
from Patterns.Oscillators import *
from Patterns.Spaceships import *
from Patterns.starters import *

vec = pg.Vector2
patterns = {"oscillators": {"blinker": blinker, "toad": toad, "beacon": beacon, "pulsar": pulsar},
            "still_lifes": {"block": block, "beehive": beeHive, "loaf": loaf},
            "spaceships": {"glider": glider, "spaceship_l": spaceshipLight,
                           "spaceship_m": spaceshipMiddle, "spaceship_h": spaceshipHeavy},
            "starters": {"acorn": acorn}}

move_directions = {
    pg.K_UP: vec(0, -1),
    pg.K_DOWN: vec(0, 1),
    pg.K_LEFT: vec(-1, 0),
    pg.K_RIGHT: vec(1, 0)
}


def create_grid_surface(grid: np.ndarray, surf_size: pg.Vector2,
                        colour=Colours.black, border=False, border_width=2) -> pg.Surface:
    grid_surf = pg.Surface(surf_size, pg.SRCALPHA)

    cell_size = vec(surf_size.x / grid.shape[1],
                    surf_size.y / grid.shape[0])

    for rowIdx, row in enumerate(grid):
        for colIdx, cell in enumerate(row):
            rect = pg.Rect([colIdx * cell_size.x, rowIdx * cell_size.y], cell_size)
            if cell:
                # print(rowIdx, colIdx)

                pg.draw.rect(grid_surf, colour.value, rect)
            else:
                pass
                # pg.draw.rect(grid_surf, Colours.green.value, rect)

    return grid_surf


class Pattern(pg.sprite.Sprite):
    def __init__(self, category, name, cell_size, pos=vec(10, 10), id=None):
        super().__init__()
        self.grid_pattern: np.ndarray = patterns[category][name]
        self.cell_size = cell_size.x
        # print(cell_size)
        self.surf_size = cell_size.x * (vec(self.grid_pattern.shape[1], self.grid_pattern.shape[0]))
        # print(surf_size)
        self.image = create_grid_surface(self.grid_pattern, self.surf_size)
        self.rect = pg.Rect(cell_size.x * pos, self.image.get_size())
        self.object_type = "pattern"
        self.pos = pos
        self.id = id
        self.shape = vec(self.grid_pattern.shape)

        self.edge_position = {"left": False, "right": False, "top": False, "bottom": False}

    def update_colour(self, colour: Colours):
        self.image = create_grid_surface(self.grid_pattern, self.surf_size,
                                         colour=colour)

    def update_position(self, pos, grid_size: vec):
        self.pos = pos
        self.rect = pg.Rect(self.cell_size * self.pos, self.image.get_size())

        self.edge_position["left"] = pos.x == 0
        self.edge_position["top"] = pos.y == 0
        self.edge_position["right"] = (pos.x == (grid_size.x - self.shape.x))
        self.edge_position["bottom"] = (pos.y == (grid_size.y - self.shape.y))

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            return True
        else:
            return False

    def click_return(self):
        return self.object_type, self.id


class GameOfLife:
    def __init__(self, cells: int = 80, frameless: bool = False, border: bool = False, border_width: int = 2,
                 enable_async=False):
        """

        :param cells: number of cells to have within the grid.
        :param frameless:
        :param grid:
        :param grid_width:
        """

        # grid definition
        self.gridSize = vec(cells, cells)
        self.grid = np.zeros([cells, cells])
        self.grid_init = None

        # kernel (game rules) definition
        self.kernel = np.ones([3, 3])
        self.kernel[1, 1] = 0

        # game properties
        self.running = True
        self.fps = 100
        self.iteration = 0
        self.population = 0
        self.started = False

        # graphics initialisation
        self.display_size, self.touch_size = vec(800, 800), vec(200, 800)
        self.border, self.border_width = border, border_width

        self.cell_size = vec(self.display_size.x / self.gridSize.x,
                             self.display_size.y / self.gridSize.y)

        print(self.cell_size)

        if self.border:
            # Add additional space for grid lines
            self.display_size += vec(border_width * (cells + 1), border_width * (cells + 1))
            self.touch_size.y = self.display_size.y

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

        self.display_screen = TouchScreen(self.display_size, colour=Colours.white)
        self.touch_screen = TouchScreen(self.touch_size, colour=Colours.midGrey)

        if self.border:
            for row_idx in range(cells + 1):
                grid_rect = pg.Rect((0, self.border_width + (self.border_width + self.cell_size) * row_idx),
                                    (self.display_size.x, self.border_width))
                pg.draw.rect(self.display_screen.base_surface, Colours.lightGrey.value, grid_rect)
            for col_idx in range(cells + 1):
                grid_rect = pg.Rect((self.border_width + (self.border_width + self.cell_size) * col_idx, 0),
                                    (self.border_width, self.display_size.y))
                pg.draw.rect(self.display_screen.base_surface, Colours.lightGrey.value, grid_rect)

        self.touch_screen.add_multiline_text("Add Patterns", base=True, rect=pg.Rect(0, 120, self.touch_size.x, 50),
                                             location=BlitLocation.topLeft, bg_colour=Colours.lightGrey,
                                             center_vertical=True,
                                             center_horizontal=True)

        self.touch_screen.add_multiline_text("Speed control", base=True, rect=pg.Rect(0, 540, self.touch_size.x, 50),
                                             location=BlitLocation.topLeft, bg_colour=Colours.lightGrey,
                                             center_vertical=True,
                                             center_horizontal=True)

        gap = 10
        labels = ["10", "100", "1000"]
        count = len(labels)

        self.likert_buttons = []
        for idx in range(count):
            width = (self.touch_size.x - (count + 1) * gap) / count
            position = gap + idx * ((self.touch_size.x - (count + 1) * gap) / count + gap)
            button = GameButton(pg.Vector2(position, (self.touch_size.y - 150) / 2), pg.Vector2(width, 150), idx,
                                text=labels[idx], )
            self.likert_buttons.append(button)

        self.back_button = GameButton((25, 500), size=vec(150, 50), id="back",
                                      text="Back", colour=Colours.hero_blue)

        self.reset_button = GameButton((18, 725), pg.Vector2(70, 50),
                                       id=1, text="Reset", colour=Colours.red)

        self.end_button = GameButton((107, 725), pg.Vector2(70, 50),
                                     id="end", text="End", colour=Colours.red)

        self.category_buttons = [GameButton(position=(25, 180 + 75 * idx),
                                            size=(150, 50), id=name, text=name.replace("_", " ").title())
                                 for idx, name in enumerate(patterns.keys())]
        self.category_buttons.append(self.reset_button)
        self.category_buttons.append(self.end_button)

        self.button_sets = {cat_name:
                                [GameButton(position=(25, 180 + 75 * idx), size=(150, 50), id=name,
                                            text=name.replace("_", " ").title()) for idx, name in
                                 enumerate(patterns[cat_name].keys())] for cat_name in patterns.keys()}

        for button_set in self.button_sets.values():
            button_set.append(self.back_button)

        self.button_sets["category"] = self.category_buttons

        self.touch_screen.sprites = GameObjects(self.button_sets["category"])

        # self.touch_screen.sprites.add(self.back_button)

        self.show_sprites = True

        self.update_display()

        self.pattern_category = None
        self.pattern_select = False

        self.pattern_count = {pattern_type: {
            pattern_name: 0 for pattern_name in patterns[pattern_type].keys()
        } for pattern_type in patterns.keys()}

        self.selected_pattern = None

        self.enable_async = enable_async

    def update_display(self, display_screen=None, touch_screen=None):
        if display_screen is None:
            display_screen = self.display_screen
        if touch_screen is None:
            touch_screen = self.touch_screen

        self.touch_screen.refresh()
        self.touch_screen.add_multiline_text(f"Iteration: {self.iteration}", pg.Rect(0, 30, self.touch_size.x, 30))
        self.touch_screen.add_multiline_text(f"Population: {self.population}", pg.Rect(0, 80, self.touch_size.x, 30))

        self.left_screen.blit(display_screen.get_surface(self.show_sprites), (0, 0))
        self.right_screen.blit(touch_screen.get_surface(), (0, 0))

        # pg.display.set_caption(str.format("Iteration: {}", self.iteration))
        pg.display.flip()

    def addPattern(self, category, name, position: vec):
        pattern_idx = self.pattern_count[category][name]
        new_pattern = Pattern(category, name, self.cell_size, pos=position,
                              id=f"{name}_{pattern_idx}")

        self.pattern_count[category][name] += 1

        self.display_screen.sprites.add(new_pattern)

        # pattern: np.ndarray = patterns[category][name]
        # self.grid[int(position.y): int(position.y) + pattern.shape[0],
        # int(position.x): int(position.x) + pattern.shape[1]] = pattern

    def iterate_grid(self):
        neighbours = cv2.filter2D(self.grid, -1, self.kernel, borderType=cv2.BORDER_CONSTANT)

        newGrid = np.zeros(self.grid.shape)

        newGrid[np.logical_and(neighbours == 3, self.grid == 0)] = 1
        newGrid[np.logical_and(np.logical_or(neighbours == 2, neighbours == 3), self.grid == 1)] = 1

        self.grid = newGrid
        self.iteration += 1

        self.population = np.count_nonzero(self.grid)

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
        self.iterate_grid()
        self.load_update()
        self.update_display()

    def get_relative_mose_pos(self):
        mouse_pos = pg.mouse.get_pos()

        if vec(mouse_pos).x <= self.display_size.x:
            return "disp", mouse_pos
        else:
            return "control", mouse_pos - vec(self.display_size.x, 0)

    def get_grid_square(self, pos):
        ...

    def finalise_grid(self):
        print("finalising grid")
        # self.grid_init = self.display_screen.sprites.copy()

        for pattern in self.display_screen.sprites:
            pattern: Pattern

            grid_section = self.grid[int(pattern.pos.y): int(pattern.pos.y + pattern.shape.x),
                           int(pattern.pos.x): int(pattern.pos.x + pattern.shape.y)]

            grid_section = np.logical_or(grid_section, pattern.grid_pattern)

            self.grid[int(pattern.pos.y): int(pattern.pos.y + pattern.shape.x),
            int(pattern.pos.x): int(pattern.pos.x + pattern.shape.y)] = grid_section

        # self.display_screen.kill_sprites()
        self.show_sprites = False
        self.update_display()

    async def run(self):
        # self.load_update()
        self.update_display()
        self.grid_init = self.display_screen.sprites.copy()

        auto = False
        start = time.monotonic()
        while self.running:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.MOUSEBUTTONDOWN:
                    screen, pos = self.get_relative_mose_pos()

                    if screen == "disp":
                        click_test = self.display_screen.click_test(pos)
                    else:
                        click_test = self.touch_screen.click_test(pos)

                    if click_test:
                        (obj_type, obj_id) = click_test
                        if obj_type == "button":
                            if obj_id == 1:
                                # restart button
                                self.show_sprites = True
                                self.grid = np.zeros([int(self.gridSize.x), int(self.gridSize.y)])
                                self.iteration = 0
                                self.started = False
                                self.display_screen.refresh()

                            elif obj_id == "back":
                                self.touch_screen.sprites = GameObjects(self.category_buttons)
                                self.touch_screen.refresh()
                                self.update_display()
                                self.pattern_select = False

                            elif obj_id == "end":
                                auto = False

                            elif self.pattern_select:
                                self.addPattern(self.pattern_category, obj_id, vec(10, 10))

                            else:
                                self.touch_screen.sprites = GameObjects(self.button_sets[obj_id])
                                self.touch_screen.refresh()
                                self.pattern_select = True
                                self.pattern_category = obj_id

                                print(self.show_sprites)

                        elif obj_type == "pattern":
                            if not self.selected_pattern:
                                # Select new pattern
                                self.selected_pattern: Pattern = self.display_screen.get_object(obj_id)
                                self.selected_pattern.update_colour(Colours.red)

                            elif obj_id != self.selected_pattern.id:
                                # Switch selected pattern
                                self.selected_pattern.update_colour(Colours.black)
                                self.selected_pattern: Pattern = self.display_screen.get_object(obj_id)
                                self.selected_pattern.update_colour(Colours.red)
                            else:
                                # De-select pattern
                                self.selected_pattern.update_colour(Colours.black)
                                self.selected_pattern = None

                        self.load_update()
                        self.update_display()

                elif event.type == pg.KEYDOWN:
                    if not self.started and self.selected_pattern is not None:
                        new_pos = self.selected_pattern.pos

                        if event.key in move_directions:
                            keyup = False
                            while not keyup:

                                move_events = pg.event.get()
                                for move_event in move_events:
                                    if move_event.type == pg.KEYUP:
                                        keyup = True

                                if event.key == pg.K_LEFT:
                                    if not self.selected_pattern.edge_position["left"]:
                                        new_pos += vec(-1, 0)
                                elif event.key == pg.K_RIGHT:
                                    if not self.selected_pattern.edge_position["right"]:
                                        new_pos += vec(1, 0)
                                elif event.key == pg.K_DOWN:
                                    if not self.selected_pattern.edge_position["bottom"]:
                                        new_pos += vec(0, 1)
                                elif event.key == pg.K_UP:
                                    if not self.selected_pattern.edge_position["top"]:
                                        new_pos += vec(0, -1)

                                self.selected_pattern.update_position(new_pos, self.gridSize)
                                self.load_update()
                                self.update_display()

                                # Use to control movement speed of the patterns pre-initiation
                                pg.time.wait(50)
                                await asyncio.sleep(0)

                    elif self.started:
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
                        if not self.started:
                            self.grid_init = self.display_screen.sprites.copy()
                            self.finalise_grid()
                            self.started = True
                        else:
                            ...

                        auto = not auto
                        start = time.monotonic()

            if auto:
                if time.monotonic() - start >= (1 / self.fps):
                    start = time.monotonic()
                    self.process_iteration()

            await asyncio.sleep(0)


if __name__ == "__main__":
    pg.init()

    game = GameOfLife(border=False, cells=200)

    game.addPattern("oscillators", "toad", vec(13, 0))
    game.addPattern("spaceships", "glider", vec(2, 3))
    game.addPattern("spaceships", "glider", vec(6, 4))
    game.addPattern("oscillators", "pulsar", vec(11, 16))
    game.addPattern("oscillators", "pulsar", vec(26, 20))

    game.addPattern("oscillators", "beacon", vec(10, 11))
    game.addPattern("spaceships", "spaceship_l", vec(4, 10))
    game.addPattern("starters", "acorn", vec(120, 120))

    asyncio.run(game.run())

