from cocos.director import director
import pyglet.font
import pyglet.resource
from mainMenu import newMenu









if __name__ == '__main__':
    pyglet.resource.path.append('code')
    pyglet.resource.reindex()
    pyglet.font.add_file('code/Oswald-Regular.ttf')

    director.init(caption='Hit A Ball')
    director.run(newMenu())