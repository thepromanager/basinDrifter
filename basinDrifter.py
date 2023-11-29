import pygame
import random
import time
import os
import math

screenWidth = 1300
screenHeight = 700
gridSize = 64
gameDisplay = pygame.display.set_mode((screenWidth, screenHeight))
clock = pygame.time.Clock()

def loadImage(textureName, size=gridSize):
    name = os.path.join("textures", textureName)
    image = pygame.image.load(name).convert_alpha()
    image = pygame.transform.scale(image, (size, size))

    #img_surface = image
    #image = pygame.transform.flip(image, True, False)
    return image

def blitRotate(surf,image, pos, originPos, angle):

    #ifx rad ddeg
    angle = -angle*180/math.pi

    # calcaulate the axis aligned bounding box of the rotated image
    w, h       = image.get_size()
    box        = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]
    min_box    = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box    = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

    # calculate the translation of the pivot 
    pivot        = pygame.math.Vector2(originPos[0], -originPos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move   = pivot_rotate - pivot

    # calculate the upper left origin of the rotated image
    origin = (int(pos[0] - originPos[0] + min_box[0] - pivot_move[0]), int(pos[1] - originPos[1] - max_box[1] + pivot_move[1]))

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle+180)
    surf.blit(rotated_image, origin)

class World():
    def __init__(self):
        self.player=None
        self.things = []
    
    def generateWorld(self): 
        self.player = Player()
        self.player.vehicle = RaceCar(20,20)
    def update(self):
        for thing in self.things:
            thing.update()
        self.player.update()
    def draw(self):
        self.player.draw()
class Player():
    idleImage = loadImage("player.png")
    def __init__(self, x=20, y=20):
        self.x = x
        self.y = y
        self.size = 1
        self.speed = gridSize//32
        self.image = Player.idleImage
        self.vehicle = None
    def update(self):
        pressed = pygame.key.get_pressed()
        if(not self.vehicle):
            self.move(pressed)
        else:
            self.vehicle.update()
            self.vehicle.move(pressed)
            self.x=self.vehicle.x
            self.y=self.vehicle.y

        #if(not pressed[pygame.K_e]):
        #    self.eDown = False
        #if(pressed[pygame.K_e] and not self.eDown):
        #    self.eDown = True
        #    self.use()
    def move(self, pressed):
        speed = self.speed
        if(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]):
            self.x+=speed
        if(pressed[pygame.K_a] or pressed[pygame.K_LEFT]):
            self.x-=speed
        if(pressed[pygame.K_s] or pressed[pygame.K_DOWN]):
            self.y+=speed
        if(pressed[pygame.K_w] or pressed[pygame.K_UP]):
            self.y-=speed
    def draw(self):
        if(self.vehicle):
            self.vehicle.draw()
        else:
            gameDisplay.blit(self.image,(self.x,self.y)) #-gridSize*self.size

class Vehicle():
    idleImage = loadImage("player.png")
    def __init__(self, x=20, y=20):
        self.x = x
        self.y = y
        self.angle = 0
        self.vx = 0
        self.vy = 0

        self.topspeed = 10
        self.acc = 0.5
        self.friction = 0.99
        self.braking = 0.9
        self.handling = 0.1
        self.traction = 0.1
        self.turnTraction = 10
        #self.drift = 
        self.image = None
    def update(self):
        self.x+=self.vx
        self.y+=self.vy
        self.vx*=self.friction
        self.vy*=self.friction
        tot=self.totalSpeed()
        if(tot!=0):
            speedRemainder=max(tot-self.traction,0)
            traction=tot-speedRemainder
            tractionx = math.cos(self.angle)*traction
            tractiony = math.sin(self.angle)*traction
            remainderx= self.vx*speedRemainder/tot
            remaindery= self.vy*speedRemainder/tot
            self.vx=tractionx+remainderx
            self.vy=tractiony+remaindery
        #pressed = pygame.key.get_pressed()
        #self.move(pressed)
        #if(not pressed[pygame.K_e]):
        #    self.eDown = False
        #if(pressed[pygame.K_e] and not self.eDown):
        #    self.eDown = True
        #    self.use()
    def move(self, pressed):
        if(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]):
            self.turn(1)
        if(pressed[pygame.K_a] or pressed[pygame.K_LEFT]):
            self.turn(-1)
        if(pressed[pygame.K_s] or pressed[pygame.K_DOWN]):
            self.brake()
        if(pressed[pygame.K_w] or pressed[pygame.K_UP]):
            self.accelerate()
    def turn(self,direction):
        tot=self.totalSpeed()
        self.angle+=direction*self.handling*min(self.turnTraction,tot)/self.topspeed

    def totalSpeed(self):
        return (self.vx**2+self.vy**2)**(1/2)

    def brake(self):
        self.vx*=self.braking
        self.vy*=self.braking
        self.vx-= math.cos(self.angle)*self.acc
        self.vy-= math.sin(self.angle)*self.acc
    
    def accelerate(self):
        if(self.totalSpeed()<self.topspeed):
            self.vx+= math.cos(self.angle)*self.acc
            self.vy+= math.sin(self.angle)*self.acc
        
    def draw(self):
        blitRotate(gameDisplay, self.image, (self.x,self.y), (gridSize//2, gridSize//2), self.angle-math.pi/2)
        #gameDisplay.blit(self.image,(self.x,self.y)) #-gridSize*self.size

class RaceCar(Vehicle):
    idleImage = loadImage("car.png")
    def __init__(self, x=20, y=20):
        super().__init__(x,y)
        self.image = RaceCar.idleImage

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # DO THINGS
        world.update()


        # DRAW
        gameDisplay.fill((25,25,105))
        world.draw()

        pygame.display.update() # flip?
        clock.tick(60)

    pygame.quit()
    quit()


world = World() 
world.generateWorld()
main()