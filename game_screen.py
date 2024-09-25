from screen import Screen, GameObjects, GameButton, Colours

class TouchScreen(Screen):
    def __init__(self, size, info_height=0.2, avatar=None, colour=Colours.white):
        super().__init__(size, colour=colour)

        self.sprites = GameObjects([])

    def click_test(self, pos):
        if self.sprites:
            for sprite in self.sprites:
                if sprite.is_clicked(pos):
                    return sprite.click_return()

        return None

    def kill_sprites(self):
        self.sprites.empty()

    def get_surface(self):
        if self.power_off:
            return self.power_off_surface

        self.sprites.draw(self)
        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def get_object(self, object_id):
        for game_object in self.sprites:
            if game_object.id == object_id:
                return game_object