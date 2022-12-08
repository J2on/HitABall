import cocos
import cocos.layer
from cocos.menu import *
import cocos.actions as ac

        
class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__('HIT A BALL')

        self.font_title['font_name'] = 'Oswald'
        self.font_title['font_size'] = 60
        self.font_title['bold'] = True
        self.font_item['font_name'] = 'Oswald'
        self.font_item_selected['font_name'] = 'Oswald'

        self.selDifficulty = 0
        self.difficulty = ['Easy', 'Normal', 'Hard']

        items = list()
        items.append(MenuItem('New Game', self.start_game))
        items.append(MultipleMenuItem('Difficuly: ', self.set_difficulty, self.difficulty, 0))
        items.append(MenuItem('Quit', exit))

        self.create_menu(items, ac.ScaleTo(1.25, duration=0.25), ac.ScaleTo(1.0, duration=0.25))

    def start_game(self):
        scene = cocos.scene.Scene()
        color_layer = cocos.layer.ColorLayer(0, 100, 0, 255)
        hud_layer = HUD()
        scene.add(hud_layer, z=2)
        scene.add(GameLayer(self.selDifficulty, hud_layer), z=1)
        scene.add(color_layer, z=0)
        cocos.director.director.push(scene)
        

    def set_difficulty(self, index):
        self.selDifficulty = index

def newMenu():
    scene = cocos.scene.Scene()
    color_layer = cocos.layer.ColorLayer(205, 133, 63, 255)
    scene.add(MainMenu(), z=1)
    scene.add(color_layer, z=0)
    return scene