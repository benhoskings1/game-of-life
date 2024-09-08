import asyncio
import pygame as pg
from game import GameOfLife



vec = pg.Vector2
pg.init()

clock = pg.time.Clock()

pg.display.set_mode((320, 240))


async def main():
    count = 60

    pg.event.pump()

    game = GameOfLife()
    game.addPattern("Toad", vec(8, 0))
    game.addPattern("Glider", vec(2, 3))
    game.addPattern("Glider", vec(7, 3))
    game.addPattern("Pulsar", vec(30, 20))
    game.addPattern("Spaceship H", vec(4, 10))
    game.addPattern("Beacon", vec(20, 25))

    while True:
        print(f"{count}: Hello from Pygame")
        pg.display.update()
        await asyncio.sleep(0)  # You must include this statement in your main loop. Keep the argument at 0.

        game.run()

        if not count:
            pg.quit()
            return

        count -= 1
        clock.tick(60)


if __name__ == '__main__':
    asyncio.run(main())
