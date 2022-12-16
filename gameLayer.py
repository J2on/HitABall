import pygame
import cocos
import cocos.layer
import random
import time
import math
import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm
import pyglet.resource

from cocos.menu import *

from collections import defaultdict
from enum import Enum
from pyglet.window import key
import pyglet.image
from pyglet.image import Animation

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
        #self.add(self.scoreText)

    

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
    
    def showText(self, textInput):
        self.anyText = cocos.text.Label(text=textInput, position=(400, 400), font_size = 200)
        print(22)
        self.add(self.anyText)
        time.sleep(1)

    def hideText(self):
        self.remove(self.anyText)

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
    
    def __init__(self, hudInput):
        super(GameLayer, self).__init__()

        self.hud = hudInput
        
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
        self.pitcher = Pitcher('asset/pitcherInit.png',400, 575)
        #self.add(self.pitcher)

        self.psuedoHitter = cocos.sprite.Sprite('asset/hitter.png', position = (370 ,150), scale = 0.2)
        self.add(self.psuedoHitter)

        self.hitter = Hitter('asset/hitterInit.png',280, 190) # 150 ~ 230

        self.catcher = Catcher(400, 90) # 110까지 
        self.add(self.catcher)

        self.homeScoreText = cocos.sprite.Sprite('asset/score0.png', position=(20, 20), scale= 1)
        self.awayScoreText = cocos.sprite.Sprite('asset/score0.png', position=(80, 20), scale= 1)

        self.add(self.homeScoreText)
        self.add(self.awayScoreText)

        #self.inGamePitcher = Pitcher(400, 570)
        #self.backBoard = cocos.sprite.Sprite('asset/backBoard.png', position = (40 ,40), scale = 1)
        #self.add(self.backBoard)
        self.updateBillBoard(self.strikeCount,self.ballCount,self.outCount,self.baseSet)
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
            if(self.outCount == 3):
                self.gameEnd()

            if(self.isInGameBgSet == False):
                self.inGameSet(self.strikeCount, self.ballCount, self.outCount)
            
            if(enter_pressed or self.pitcher.ANIMPLAYING):
                print(self.pitcher.ANIMPLAYING)
                self.pitcher.pitch()
                
                if(self.pitcher.ANIMPLAYING == False):
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
                elif((obj == self.hitter and space_pressed) or self.hitter.ANIMPLAYING):
                    self.hitter.swing()

                    if(self.hitter.ANIMPLAYING == False):
                        self.add(self.ball.shadow)
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
                
                self.ball.shadow.kill()
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
                self.ball
                self.newHitter()
                
                return True
        return False
    def gameEnd(self):
        self.gameEndText = cocos.sprite.Sprite('asset/GameEnd.png', position=(400, 400), scale= 1)
        self.add(self.gameEndText)
        time.sleep(999)

    def hitUpdate(self):
        #거리가 560 이상이면 호무런 self.homeX, self.homeY 랑 fallingPos랑 거리를 구하기
        flyingDistance = math.sqrt((self.ball.fallingPos[0] - float(self.homeX))**2 + (self.ball.fallingPos[1] - float(self.homeY))**2)
        
        if(self.baseSet[0] or self.baseSet[1] or self.baseSet[2]):
                self.remove(self.BaseBoard)
        
        if(flyingDistance > 560):
            homerunScore = 1
            for i in range(3):
                if(self.baseSet[i] == True):
                    homerunScore += 1
                    self.baseSet[i] = False
            self.homerunText = cocos.sprite.Sprite('asset/HomeRun.png', position=(400, 400), scale= 1)
            self.add(self.homerunText)
            self.homeScore += homerunScore
            time.sleep(1)
            self.homerunText.kill()
        else:
            self.hud.showText('Hit!')
            self.hud.hideText()
            if(self.baseSet[2] == True):
                self.homeScore += 1
            self.baseSet[2] = self.baseSet[1]
            self.baseSet[1] = self.baseSet[0]
            self.baseSet[0] = True
            self.hitText = cocos.sprite.Sprite('asset/Hit.png', position=(400, 400), scale= 1)
            self.add(self.hitText)
            
            time.sleep(0.5)
            self.hitText.kill()

        self.newHitter()
        
    def newHitter(self):
        if(self.strikeCount != 0):
            self.remove(self.strikeBoard)
        if(self.ballCount != 0):
            self.remove(self.ballBoard) 

        
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
            if(self.baseSet[2] == True):
                self.homeScore += 1
            self.baseSet[2] = self.baseSet[1]
            self.baseSet[1] = self.baseSet[0]
            self.baseSet[0] = True
            self.newHitter()

    
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

        self.remove(self.homeScoreText)
        self.remove(self.awayScoreText)

        if(self.homeScore == 0):
            self.homeScoreText = cocos.sprite.Sprite('asset/score0.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 1):
            self.homeScoreText = cocos.sprite.Sprite('asset/score1.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 2):
            self.homeScoreText = cocos.sprite.Sprite('asset/score2.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 3):
            self.homeScoreText = cocos.sprite.Sprite('asset/score3.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 4):
            self.homeScoreText = cocos.sprite.Sprite('asset/score4.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 5):
            self.homeScoreText = cocos.sprite.Sprite('asset/score5.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 6):
            self.homeScoreText = cocos.sprite.Sprite('asset/score6.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 7):
            self.homeScoreText = cocos.sprite.Sprite('asset/score7.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 8):
            self.homeScoreText = cocos.sprite.Sprite('asset/score8.png', position=(20, 20), scale= 1)
        elif(self.homeScore == 9):
            self.homeScoreText = cocos.sprite.Sprite('asset/score9.png', position=(20, 20), scale= 1)


        if(self.awayScore == 0):
            self.awayScoreText = cocos.sprite.Sprite('asset/score0.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 1):
            self.awayScoreText = cocos.sprite.Sprite('asset/score1.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 2):
            self.awayScoreText = cocos.sprite.Sprite('asset/score2.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 3):
            self.awayScoreText = cocos.sprite.Sprite('asset/score3.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 4):
            self.awayScoreText = cocos.sprite.Sprite('asset/score4.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 5):
            self.awayScoreText = cocos.sprite.Sprite('asset/score5.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 6):
            self.awayScoreText = cocos.sprite.Sprite('asset/score6.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 7):
            self.awayScoreText = cocos.sprite.Sprite('asset/score7.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 8):
            self.awayScoreText = cocos.sprite.Sprite('asset/score8.png', position=(80, 20), scale= 1)
        elif(self.awayScore == 9):
            self.awayScoreText = cocos.sprite.Sprite('asset/score9.png', position=(80, 20), scale= 1)
        
        self.add(cocos.sprite.Sprite('asset/ddangddang.png', position=(50, 20), scale= 1))
        self.add(self.homeScoreText)
        self.add(self.awayScoreText)


    def score(self, anyTeamScore, run):
        anyTeamScore += run
        self.hud.updateScore(self.homeScore, self.awayScore)

    def inGameSet(self, strike, ball, out):
        #self.backBoard.kill()
        self.add(self.inGameBg)
        self.add(self.pitcher)
        self.pitcher.__init__('asset/pitcherInit.png', 400,575)
        self.add(self.hitter)
        self.hitter.__init__('asset/hitterInit.png', 280, 190)
        #self.add(self.backBoard)
        self.isInGameBgSet = True
        self.updateBillBoard(strike, ball, out, self.baseSet)

    def rmIngameScene(self):
        #self.backBoard.kill()
        self.isInGameBgSet = False
        self.remove(self.inGameBg)
        self.remove(self.pitcher)
        self.remove(self.hitter)
        #self.add(self.backBoard)

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
    ANIMSTATE = 0
    ANIMPLAYING = False
    #raw = pyglet.image.load_animation('asset/pitcherAnim.gif')
    #cocos.sprite.
    #seq = pyglet.image.ImageGrid(raw, 290, 299)
    #pitcher_img = Animation.from_image_sequence(seq, 0.07, False)
    def __init__(self,imageInput,locx, locy):
        super(Pitcher, self).__init__(image= imageInput, x=locx, y=locy)
        self.setScale(0.3)
        
        print('init')

    def pitch(self):
        self.ANIMPLAYING = True
        if(self.ANIMSTATE == 0):
            self.__init__('asset/pitcherInit.png',400,575)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 1):
            self.__init__('asset/pitcherAnim1.png',400,575)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 2):
            self.__init__('asset/pitcherAnim2.png',400,575)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 3):
            self.__init__('asset/pitcherAnim3.png',400,575)
            self.ANIMSTATE = 0
            self.ANIMPLAYING = False
            GameLayer.GAMESTATE = GameState.PITCH
        time.sleep(0.15)

class Hitter(Player):
    ANIMSTATE = 0
    ANIMPLAYING = False
    def __init__(self, inputImage,x, y):
        super(Hitter, self).__init__(inputImage, x, y)
        self.cshape = cm.AARectShape((400,y),80,20)
        self.setScale(0.7)

    def swing(self):
        self.ANIMPLAYING = True
        if(self.ANIMSTATE == 0):
            self.__init__('asset/hitterInit.png',280,190)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 1):
            self.__init__('asset/hitterAnim1.png',280,190)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 2):
            self.__init__('asset/hitterAnim2.png',280,190)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 3):
            self.__init__('asset/hitterAnim3.png',280,190)
            self.ANIMSTATE += 1
        elif(self.ANIMSTATE == 4):
            self.ANIMSTATE = 0
            self.ANIMPLAYING = False
            GameLayer.GAMESTATE = GameState.DEFENCE
        time.sleep(0.02)
        

class Ball(cocos.sprite.Sprite):
    def __init__(self): 
        super(Ball, self).__init__('asset/ball.png')
        self.ballControl = random.uniform(-0.7,0.1)
        self.speed = eu.Vector2(self.ballControl, -10)
        self.cshape = cm.CircleShape((410,530), 5)
        self.position = pos = eu.Vector2(410,530)
        self.hitDegree = 0.0
        self.fallingPos = eu.Vector2()
        self.moveCount = 0
        self.shadow = cocos.sprite.Sprite('asset/ballShadow.png', position=(0, 0), scale= 0.5)
        self.shadowDepth = -20

    def setScale(self, scaleInput):
        self.scale = scaleInput

    def update(self):
        self.move()


    def move(self):
        self.position += self.speed
        self.cshape.center += self.speed
        self.moveCount += 1

        if(GameLayer.GAMESTATE == GameState.DEFENCE):
            self.shadow.position = self.position + eu.Vector2(0, self.shadowDepth)
            if(self.moveCount<25):
                self.shadowDepth -= 5
                self.scale += 0.05
            else:
                self.shadowDepth += 5
                self.scale -= 0.05
        
    
    
    def hit(self, homeX, homeY):
        self.moveCount = 0
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
        scene.add(GameLayer(hud_layer), z=1)
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