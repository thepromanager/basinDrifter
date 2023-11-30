import pygame
import random
import time
import os
import math
import numpy as np

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
        self.vehicles = []
    
    def generateWorld(self): 
        self.player = Player()
        self.vehicles.append(RaceCar(np.array([150.0, 200.0])))
        self.vehicles.append(SlowCar(np.array([200.0, 100.0])))
        self.things.append(Animus(np.array([200.0, 300.0])))

    def update(self):
        for vehicle in self.vehicles:
            vehicle.update()
        for thing in self.things:
            thing.update()
        self.player.update()

    def draw(self):
        for vehicle in self.vehicles:
            vehicle.draw()
        for thing in self.things:
            thing.draw()
        self.player.draw()
    def setInbounds(self,pos):
        x=pos[0]
        y=pos[1]
        if(x>1300):
            x-=1300
        if(x<0):
            x+=1300
        if(y>700):
            y-=700
        if(y<0):
            y+=700
        return np.array([x,y])

class Player():
    idleImage = loadImage("player.png")
    def __init__(self, pos=np.array([20,20])):
        self.pos = pos
        self.size = 16
        self.speed = gridSize//32
        self.image = Player.idleImage
        self.vehicle = None

    def update(self):
        pressed = pygame.key.get_pressed()
        if(not self.vehicle):
            self.move(pressed)
        else:
            self.vehicle.move(pressed)
            self.pos=self.vehicle.pos


        if(not pressed[pygame.K_LSHIFT]):
            self.shiftDown = False
        if(pressed[pygame.K_LSHIFT] and not self.shiftDown):
            self.shiftDown = True
            if self.vehicle == None:
                self.enterClosestVehicle()
            else:
                self.exitVehicle()

    def move(self, pressed):
        speed = self.speed
        if(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]):
            self.pos+=speed*np.array([1,0])
        if(pressed[pygame.K_a] or pressed[pygame.K_LEFT]):
            self.pos+=speed*np.array([-1,0])
        if(pressed[pygame.K_s] or pressed[pygame.K_DOWN]):
            self.pos+=speed*np.array([0,1])
        if(pressed[pygame.K_w] or pressed[pygame.K_UP]):
            self.pos+=speed*np.array([0,-1])

    def enterClosestVehicle(self):#, vehicle):

        # find closest vehicle
        bestDist = 50
        bestVehicle = None
        for vehicle in world.vehicles:
            dist = np.linalg.norm(vehicle.pos - self.pos)
            print(dist, bestDist)
            if dist < bestDist:
                bestDist = dist
                bestVehicle = vehicle

        # enter
        if bestVehicle:
            self.vehicle = bestVehicle

    def exitVehicle(self):
        self.vehicle = None
       
    def draw(self):
        if(self.vehicle):
            self.vehicle.draw()
        else:
            gameDisplay.blit(self.image,self.pos+np.array([-32.0,-32.0])) #-gridSize*self.size

class Enemy(): # or creature rather

    def __init__(self, pos=np.array([20.0,20.0])):
        self.pos = pos
        self.size = 16
        self.angle = 0
        self.vehicle = None

    def update(self):
        pass

    def hurt(self, damage):
        if damage > 10:
            if self in world.things:
                world.things.remove(self)

    def draw(self):
        blitRotate(gameDisplay, self.image, self.pos, (gridSize//2, gridSize//2), self.angle-math.pi/2)
        
class Animus(Enemy): # because
    images = [loadImage("things/beetle/beetle1.png"),loadImage("things/beetle/beetle2.png")]
    def __init__(self, pos=np.array([20.0,20.0])):
        super().__init__(pos)
        self.image = Animus.images[0]
        self.size = 16

    def update(self):
        direction = world.player.pos - self.pos
        direction = direction/np.linalg.norm(direction)
        self.angle = np.arctan2(direction[1], direction[0])
        self.pos += direction
        self.image = Animus.images[random.randint(0,1)]


class Vehicle():
    idleImage = loadImage("player.png")
    def __init__(self, pos=np.array([20.0,20.0])):
        self.size = 16
        self.pos = pos
        self.angle = 0.0
        self.vel = np.array([0.0,0.0])

        self.topspeed = 10.0
        self.acc = 0.3
        self.sideFriction = 0.95
        self.forwardFriction = 0.99
        self.braking = 0.9
        self.handling = 0.1
        #self.traction = 0.1
        #self.turnTraction = 10.0
        #self.drift = 
        self.image = None
    def direction(self,shift=0):
        return np.array([np.cos(self.angle+shift),np.sin(self.angle+shift)])

    def update(self):

        # move
        self.pos+=self.vel

        # friction
        #self.vel=self.friction*self.vel
        tot=self.totalSpeed()
        if(tot!=0):
            forwardVel = self.direction()*(np.dot(self.vel,self.direction()))*self.forwardFriction
            sideVel = self.direction(np.pi/2)*(np.dot(self.vel,self.direction(np.pi/2)))*self.sideFriction
            print(self.vel)
            self.vel = forwardVel + sideVel
            print(self.vel)
            """
            speedRemainder=max(tot-self.traction,0)
            traction=tot-speedRemainder
            traction = traction*self.direction()
            remainder= self.vel*speedRemainder/tot
            self.vel=traction+remainder
            """

        for i in world.things + world.vehicles: #collidibles ?
            if i != self:
                if np.linalg.norm(self.pos - i.pos)<self.size + i.size:
                    self.collide(i)

        # inbounds
        self.pos=world.setInbounds(self.pos)

    def collide(self, other):
        speed = np.linalg.norm(self.vel)
        other.hurt(speed*self.size/16) #mass?
        self.vel *= 0

    def hurt(self, damage):
        pass

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
        self.angle+=direction*self.handling*tot/self.topspeed#min(self.turnTraction,

    def totalSpeed(self):
        return np.linalg.norm(self.vel)

    def brake(self):
        self.vel*=self.braking
        self.vel-=self.acc*self.direction()
    
    def accelerate(self):
        if(self.totalSpeed()<self.topspeed):
            self.vel+=self.acc*self.direction()
        
    def draw(self):
        blitRotate(gameDisplay, self.image, self.pos, (gridSize//2, gridSize//2), self.angle-math.pi/2)
        #gameDisplay.blit(self.image,(self.x,self.y)) #-gridSize*self.size

class RaceCar(Vehicle):
    idleImage = loadImage("vehicles/car.png")
    def __init__(self, pos=np.array([20.0,20.0])):
        super().__init__(pos)
        self.image = RaceCar.idleImage

        self.topspeed = 10.0
        self.acc = 0.3
        self.sideFriction = 0.95
        self.forwardFriction = 0.99
        self.braking = 0.9
        self.handling = 0.1
class SlowCar(Vehicle):
    idleImage = loadImage("vehicles/car2.png")
    def __init__(self, pos=np.array([20.0,20.0])):
        super().__init__(pos)
        self.image = SlowCar.idleImage

        self.topspeed = 5.0
        self.acc = 0.15
        self.sideFriction = 0.95
        self.forwardFriction = 0.98
        self.braking = 0.95
        self.handling = 0.05

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # DO THINGS
        world.update()


        # DRAW
        gameDisplay.fill((55,105,55))
        world.draw()

        pygame.display.update() # flip?
        clock.tick(60)

    pygame.quit()
    quit()


world = World() 
world.generateWorld()
main()