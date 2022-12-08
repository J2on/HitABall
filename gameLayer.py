import pygame
import cocos
import cocos.layer
import random
import time

import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm
import pyglet.resource

from cocos.menu import *

from collections import defaultdict
from enum import Enum
from pyglet.window import key

class HUD(cocos.layer.Layer):
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()

        fontSize = 18
        fontColor = (0, 50, 0, 255)
        #self.ballCountText = cocos.text.Label(text = '', font_size = fontSize, color = fontColor)
        self.scoreText = cocos.text.Label(text='', font_size = fontSize, color = fontColor)
        #self.ballCountText.position = (20, 80)
        self.scoreText.position = (20, 40)
        #self.add(self.ballCountText)
        self.add(self.scoreText)

    

    def updateScore(self, homeScore, awayScore):
        self.scoreText.element.text = 'Home: %s Away: %s' % (homeScore, awayScore)

    def showGameOver(self, winner):
        w, h = cocos.director.director.get_window_size()
        gameOver = cocos.text.Label(winner, font_size=50,
                                     anchor_x='center',
                                     anchor_y='center',
                                     color=(50, 50, 255, 255))
        gameOver.position = w * 0.5, h * 0.5
        self.add(gameOver)

class GameState(Enum):
    DEADBALL = 1
    PITCH = 2
    DEFENCE = 3
    

class GameLayer(cocos.layer.Layer):
    GAMESTATE = GameState(1)
    KEYS_PRESSED = defaultdict(int)

    is_event_handler = True

    def on_key_press(self, k, _):
        GameLayer.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        GameLayer.KEYS_PRESSED[k] = 0
    
    def __init__(self, hudInput, difficultyInput):
        super(GameLayer, self).__init__()

        self.hud = hudInput
        self.difficulty = difficultyInput
        
        self.inning = 1
        self.homeScore = 0
        self.awayScore = 0
        
        self.strikeCount = 0
        self.ballCount = 0
        self.outCount = 0
        self.baseSet = [False, False, False]

        h = 800
        w = 800

        self.homeX = 400
        self.homeY = 105

        self.hud.updateScore(self.homeScore, self.awayScore)
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, 40, 40)
    
        self.bg = cocos.sprite.Sprite('asset/bg.png', position = (w/2 ,h/2), scale = 1)
        self.add(self.bg)

        self.inGameBg = cocos.sprite.Sprite('asset/inGamebg.png', position = (w/2 ,h/2), scale = 1)
        self.isInGameBgSet = False
        

        #self.picher = cocos.sprite.Sprite('picher.png', position = (400, 360), scale = 0.2 ,color = (255, 255, 255))
        self.pitcher = Pitcher(400, 575)
        self.pitcher.setScale(0.3)
        #self.add(self.pitcher)

        self.psuedoHitter = cocos.sprite.Sprite('asset/hitter.png', position = (370 ,150), scale = 0.2)
        self.add(self.psuedoHitter)

        self.hitter = Hitter(280, 190) # 150 ~ 230
        self.hitter.setScale(0.7)

        self.catcher = Catcher(400, 90) # 110까지 
        self.add(self.catcher)

        #self.inGamePitcher = Pitcher(400, 570)
        

        self.ball = Ball()

        self.defencePosition = [[550,350],[480,440],[250,350],[320,440],[170,550],[400,600],[630,550], [400, 320]]

        for pos in self.defencePosition:
            self.baseMan = BaseMan(pos[0], pos[1])
            self.add(self.baseMan)

        # 스케쥴은 매 틱마다 함수를 호출
        self.schedule(self.update)

    def update(self, dt):
        pressed = GameLayer.KEYS_PRESSED
        space_pressed = pressed[key.SPACE] == 1
        enter_pressed = pressed[key.ENTER] == 1

        if(GameLayer.GAMESTATE == GameState.DEADBALL):
            if(self.isInGameBgSet == False):
                self.inGameSet(self.strikeCount, self.ballCount, self.outCount)
            
            if(enter_pressed):
                GameLayer.GAMESTATE = GameState.PITCH
                self.ball.__init__()
                self.add(self.ball)

        elif(GameLayer.GAMESTATE == GameState.PITCH):
            self.collman.clear()
            self.collman.add(self.catcher)
            self.collman.add(self.hitter)
            self.ball.update()
            
            
            for obj in self.collman.iter_colliding(self.ball):
                if(obj == self.catcher):
                    GameLayer.GAMESTATE = GameState.DEADBALL
                    self.ball.kill()
                    print(obj.position)
                    if(self.ball.ballControl > -0.5 and self.ball.ballControl < -0.1):
                        self.strikeCall()
                    else:
                        self.ballCall()
                    self.rmIngameScene()
                    time.sleep(1)
                elif(obj == self.hitter and space_pressed):
                    GameLayer.GAMESTATE = GameState.DEFENCE
                    print(self.ball.position[1])
                    self.ball.hit(self.homeX, self.homeY)
                    self.rmIngameScene()

                
        elif(GameLayer.GAMESTATE == GameState.DEFENCE):
            print(self.ball.hitDegree)
            # 타자가 공을 친 이후 GAMESTATE ENUM이 Defence로 들어가면 낙구위치랑 수비랑 콜리전 파악 or 기울기에 따라 파울인지 확인 or 비거리에 따라 홈런인지 확인
            if(self.ball.fallingPos[1] > self.ball.position[1]):
                self.ball.update()
                
            else:
                if(self.foulCheck()):
                    # 이미  foulCheck함수에서 할거 다 했음
                    pass
                elif(self.outCheck()): 
                    pass
                else: #### 이 부분에 안타 구현해야 함~~~~~~~
                    self.hitUpdate()
                
                
                time.sleep(1)
                GameLayer.GAMESTATE = GameState.DEADBALL
                self.ball.kill()
                    
            
            
    def foulCheck(self):
        if(self.ball.hitDegree < -1 or self.ball.hitDegree > 1):
            if(self.strikeCount == 2):
                return True
            elif(self.strikeCount == 1 or self.strikeCount == 0):
                self.strikeCount += 1
            else: self.strikeCount = 0

            return True
        return False

    def outCheck(self):
        self.collman.clear()
        for defender in (BaseMan.BASEMANLIST):
            self.collman.add(defender)
            for obj in self.collman.iter_colliding(self.ball):
                self.outCount += 1
                self.newHitter()
                return True
        return False

    def hitUpdate(self):
        if(self.baseSet[2] == True):
            self.score(self.homeScore, 1)

        self.baseSet[2] = self.baseSet[1]
        self.baseSet[1] = self.baseSet[0]
        self.baseSet[0] = True
        self.newHitter()
        
    def newHitter(self):
        self.strikeCount = 0
        self.ballCount = 0        
    
    def strikeCall(self):
        if(self.strikeCount == 0 or self.strikeCount == 1):
            self.strikeCount += 1
        else:
            self.strikeCount = 0
            self.ballCount = 0
            self.outCount += 1

    def ballCall(self):
        if(self.ballCount == 0 or self.ballCount == 1 or self.ballCount == 2):
            self.ballCount += 1
        else:
            self.ballCount = 0
            #주자 출루 볼넷 만들어야 함

    
    def updateBillBoard(self, strike, ball, out, baseSet):
        for numS in range(strike) :
            self.strikeBoard = cocos.sprite.Sprite('asset/StrikeStripe.png', position=(40 * (numS+1), 140), scale= 0.15)
            self.add(self.strikeBoard)

        for numB in range(ball) :
            self.ballBoard = cocos.sprite.Sprite('asset/BallStripe.png', position=(40 * (numB+1), 190), scale= 0.15)
            self.add(self.ballBoard)

        for numO in range(out):
            self.outBoard = cocos.sprite.Sprite('asset/OutStripe.png', position=(40 * (numO+1), 90), scale= 0.15)
            self.add(self.outBoard)

        for numBase in range(3):
            if(baseSet[numBase]):
                if(numBase == 0):
                    self.BaseBoard = cocos.sprite.Sprite('asset/BaseStripe.png', position=(70, 210), scale= 0.1)
                    self.add(self.BaseBoard)
                elif(numBase == 1):
                    self.BaseBoard = cocos.sprite.Sprite('asset/BaseStripe.png', position=(50, 230), scale= 0.1)
                    self.add(self.BaseBoard)
                elif(numBase == 2):
                    self.BaseBoard = cocos.sprite.Sprite('asset/BaseStripe.png', position=(30, 210), scale= 0.1)
                    self.add(self.BaseBoard)
    def rmBillBoard(self):
        if(self.strikeCount != 0):
            self.remove(self.strikeBoard)
        if(self.ballCount != 0):
            self.remove(self.ballBoard)
        if(self.outCount != 0):
            self.remove(self.outBoard)


    def score(self, anyTeamScore, run):
        anyTeamScore += run
        self.hud.updateScore(self.homeScore, self.awayScore)

    def inGameSet(self, strike, ball, out):
        self.add(self.inGameBg)
        self.add(self.pitcher)
        self.add(self.hitter)
                
        self.isInGameBgSet = True
        self.updateBillBoard(strike, ball, out, self.baseSet)

    def rmIngameScene(self):
        self.isInGameBgSet = False
        self.remove(self.inGameBg)
        self.remove(self.pitcher)
        self.remove(self.hitter)

class Player(cocos.sprite.Sprite):
    def __init__(self, image, x, y):
        super(Player, self).__init__(image, scale=0.2)
        self.position = eu.Vector2(x, y)
        self.cshape = cm.CircleShape((x,y), 20)
        
    def setScale(self, scaleSize):
        self.scale = scaleSize

class BaseMan(Player):
    BASEMANLIST = []
    def __init__(self, x, y):
        super(BaseMan, self).__init__('asset/defender.png', x, y)
        self.cshape = cm.CircleShape((x,y), 50)
        BaseMan.BASEMANLIST.append(self)

class Catcher(Player):
    def __init__(self, x, y):
        super(Catcher, self).__init__('asset/catcher.png', x, y)
        self.cshape = cm.CircleShape((x,y-20), 20)


class Pitcher(Player):
    def __init__(self, x, y):
        super(Pitcher, self).__init__('asset/pitcher.png', x, y)

    def pitch(self):
        GameLayer.GAMESTATE = GameState.PITCH
        print('pitch')

    def update(self): 
        print('update')


class Hitter(Player):
    def __init__(self, x, y):
        super(Hitter, self).__init__('asset/hitter.png', x, y)
        self.cshape = cm.AARectShape((400,y),80,20)
        #self.rotation = 40
    def swing(self):
    #    self.rotation -= 50
        pass   
        

class Ball(cocos.sprite.Sprite):
    def __init__(self): 
        super(Ball, self).__init__('asset/ball.png')
        self.ballControl = random.uniform(-0.7,0.1)
        self.speed = eu.Vector2(self.ballControl, -10)
        self.cshape = cm.CircleShape((410,530), 5)
        self.position = pos = eu.Vector2(410,530)
        self.hitDegree = 0.0
        self.fallingPos = eu.Vector2()

    def setScale(self, scaleInput):
        self.scale = scaleInput

    def update(self):
        self.move()
    def convert_to_2d(self):
        self.speed = eu.Vector2(self.speed[0]*(self.speed[2]*.3),self.speed[1]*(self.speed[2]*.3))
    def move(self):
        self.position += self.speed
        self.cshape.center += self.speed
    
    
    def hit(self, homeX, homeY):
        if(self.position[1] > 210):
            self.hitDegree = random.uniform(-1,-2)
        elif(self.position[1] > 190 and self.position[1] <= 210):
            self.hitDegree = random.uniform(-1.5, -0.5)
        elif(self.position[1] > 170 and self.position[1] <= 190):
            self.hitDegree = random.uniform(-0.5, 0.5)
        elif(self.position[1] == 170):
            self.hitDegree = random.uniform(0.5, 1.5)
        else:
            self.hitDegree = random.uniform(1, 2)

        randInt = random.randrange(100,580)
        self.fallingPos = eu.Vector2(homeX + self.hitDegree*randInt, homeY + randInt)

        self.speed = (self.fallingPos - self.position) / 50


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
        scene.add(GameLayer(hud_layer, self.selDifficulty), z=1)
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


if __name__ == '__main__':
    cocos.director.director.init(caption='Hit a Ball', width = 800, height = 800)

    scene = cocos.scene.Scene()
    scene.add(MainMenu())
    
    cocos.director.director.run(scene)