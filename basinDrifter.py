import pygame
import random
import time
import os
import math
import numpy as np

# tiles
# health bar
# combat
# items
# inventory

# lighting?
#inside houses?

#enemies with different behaviour, fågel, ko, 
#bombs, melee, ammo, crates filled with goodies
#biomes, chunks, rivers, roads, collide walls, structures, tiles 

screenWidth = 1400
screenHeight = 800
gridSize = 64
gameDisplay = pygame.display.set_mode((screenWidth, screenHeight))
clock = pygame.time.Clock()

def loadImage(textureName, size=gridSize):
    name = os.path.join("assets/textures", textureName)
    image = pygame.image.load(name).convert_alpha()
    image = pygame.transform.scale(image, (size, size))

    #img_surface = image
    #image = pygame.transform.flip(image, True, False)
    return image

def blitRotate(surf,image, pos, originPos, angle):

    #fix rad ddeg
    angle = 180-angle*180/np.pi

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

class Camera():

    def __init__(self, pos = np.array([0.,0.])):
        self.pos = pos
        self.angle = 0.

    def update(self):
        followSpeed = 0.5
        angleSpeed = 0.05
        self.pos = self.pos*(1-followSpeed) + world.player.pos*followSpeed
        if(world.player.vehicle and False):
            targetAngle = (world.player.angle + np.pi/2 - self.angle + np.pi) % (np.pi*2) + self.angle - np.pi # camera has player rotated 90 (so why isnt it -pi/2 ?!?)
            self.angle = self.angle*(1-angleSpeed) + targetAngle*angleSpeed

    def blitImage(self, surf, image, pos, originPos, angle):
        #cameraAngle = self.angle
        #R = np.array([[np.cos(-cameraAngle), -np.sin(-cameraAngle)],
        #              [np.sin(-cameraAngle),  np.cos(-cameraAngle)]])

        blittingPos = np.array([screenWidth//2, screenHeight//2]) + (pos - self.pos) # rotate position relative to player
        #blittingAngle = angle - cameraAngle
        #blitRotate(surf,image, blittingPos, originPos, blittingAngle)
        if(angle==0):
            surf.blit(image,(blittingPos - originPos))
        else:
            blitRotate(surf,image, blittingPos, originPos, angle)

class World():
    #groundSize = 448
    worldsize = 15 #chunks x chunks
    chunksize = 14 #tiles x tiles #14*32 = 448 och 448 är stort nog för att man inte ska se world border (laggar om den är större?)
    tilesize = 32 #pixels x pixels
    groundSize = chunksize*tilesize #448
    def __init__(self):
        self.player=None
        self.chunks = [[Chunk(random.randint(1,1000000),np.array([i,j])) for i in range(self.worldsize)] for j in range(self.worldsize)]
        self.entities = []
        self.camera = Camera()
        self.size = 1300.0
        self.centerChunk = None
        self.loadedChunks = []
        self.toBeKilled = []
        #self.surf = pygame.Surface((self.groundSize*4,self.groundSize*4)).convert_alpha()
        #for x in [0,1,2,3]:
        #    for y in [0,1,2,3]:
        #        self.surf.blit(self.groundImage,np.array([x*self.groundSize,y*self.groundSize]))
        
    def generateWorld(self):
        center=np.array([self.groundSize*self.worldsize//2,self.groundSize*self.worldsize//2]).astype("float64")
        self.player = Player(center)
        self.centerChunk = self.getChunk(center)
        self.loadChunks()
    def loadChunks(self):
        x=self.centerChunk.gridpos[0]
        y=self.centerChunk.gridpos[1]
        newChunks=[]
        for dx in [-1,0,1]:
            for dy in [-2,-1,0,1,2]: #dx and dy flipped :/
                if(0 <= x+dx and x+dx<self.worldsize and 0 <= y+dy and y+dy<self.worldsize):
                    newChunks.append(self.chunks[x+dx][y+dy])
        for entity in self.entities:
            inbounds=False
            for newChunk in newChunks:
                if(newChunk.inbounds(entity.pos)):
                    inbounds=True
            if(not inbounds):
                entity.despawn()
        for entity in self.toBeKilled:
            self.entities.remove(entity)
        self.toBeKilled=[] 
        
        for newChunk in newChunks:
            if not newChunk in self.loadedChunks:
                newChunk.load()
        self.loadedChunks=newChunks

        #self.entities.append(self.player) draw last
    def getChunk(self,pos):
        x=int(pos[0]//self.groundSize) #necessary beacuse of numpy?
        #print(pos,x)
        y=int(pos[1]//self.groundSize)
        if(0<=x and x<self.worldsize and 0<=y and y<self.worldsize):
            return self.chunks[x][y] 

        
    def update(self):
        self.player.update()
        for entity in self.entities:
            entity.update()

        self.camera.update()

    def draw(self):
        
        
         #       self.groundSize*((self.player.pos)//self.groundSize)
        #world.camera.blitImage(gameDisplay, self.surf, self.groundSize*((self.player.pos+self.groundSize//2)//self.groundSize), (self.groundSize*2, self.groundSize*2), 0)
        for chunk in world.loadedChunks:
            chunk.draw()
        for entity in self.entities:
            entity.draw()
        self.player.draw()

    def setInbounds(self,pos):
        x=pos[0]
        y=pos[1]
        if(x>self.player.pos[0]+self.size/2): # the world is a 1000x1000 torus around the player
            x-=self.size
        if(x<self.player.pos[0]-self.size/2):
            x+=self.size
        if(y>self.player.pos[1]+self.size/2):
            y-=self.size
        if(y<self.player.pos[1]-self.size/2):
            y+=self.size
        return np.array([x,y])

class Chunk():
    groundImage=loadImage("tiles/ground.png",size=World.groundSize)
    def __init__(self, seed,gridpos):
        self.seed=seed
        self.tiles=None
        self.visited=False
        self.gridpos = gridpos
        self.pos = World.groundSize*self.gridpos.astype("float64")
        self.image = self.groundImage
        #self.toBeKilled = []  # remove this? /b
    def generateTiles(self):
        random.seed(self.seed)
        self.tiles=[[0 for i in range(World.chunksize)] for j in range(World.chunksize)] #easy spatial lookup but slow iteration?
        if random.random()<0.5:
            for i in range(random.randint(4,10)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 5 # bush
        elif random.random()<0.5:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 2 # beetle
        elif random.random()<0.5:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 6 # worm
        elif random.random()<0.5:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 1 # box
        else:
            for i in range(random.randint(0,random.randint(0,1))):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 3 # slow car
            for i in range(random.randint(0,random.randint(0,1))):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 4 # race car
        self.visited=True
    def inbounds(self,pos):
        if(pos[0]>=self.pos[0] and pos[1]>=self.pos[1] and pos[0]<self.pos[0]+world.groundSize and pos[1]<self.pos[1]+world.groundSize):
            return True
        else:
            return False

    def getTilePos(self,x,y):
        return self.pos+np.array([x*World.tilesize,y*World.tilesize])
    def generateEntities(self):
        for x in range(World.chunksize): #scipy.sparse find? onödig optimisering
            for y in range(World.chunksize):
                tile=self.tiles[x][y]
                pos=self.getTilePos(x,y)+np.array([1,1])
                origin=(self,(x,y),tile) #<- tile index,
                if(tile==1): #Box
                    world.entities.append(Box(pos,origin))
                elif(tile==2): #Beetle
                    world.entities.append(Beetle(pos,origin))
                elif(tile==3): #SlowCar
                    world.entities.append(SlowCar(pos,origin))
                elif(tile==4): #RaceCar
                    world.entities.append(RaceCar(pos,origin))
                elif(tile==5): #Bush
                    world.entities.append(Bush(pos,origin))
                elif(tile==6): #Beetle
                    world.entities.append(Worm(pos,origin))
                if(tile<100): #tile numbers under 100 are entities, over 100 are other types of tiles
                    self.tiles[x][y]=0
    def load(self):
        if(not self.visited):
            self.generateTiles()
        self.generateEntities()

    def draw(self):
        world.camera.blitImage(gameDisplay, self.image, self.pos+np.array([World.groundSize,World.groundSize]), (World.groundSize,World.groundSize), 0)  


class Entity():
    def __init__(self, pos,origin):
        self.origin=origin
        self.pos = pos
        self.angle = 0.
        self.vel = np.array([0.0,0.0])
        self.size = 16 
        self.image = None
        self.health = 10
    def update(self):
        self.pos += self.vel
    def draw(self): 
        world.camera.blitImage(gameDisplay, self.image, self.pos, (gridSize//2,gridSize//2), self.angle)
    def hurt(self, damage):
        if damage >= self.health:
            self.health=0
            if self in world.entities:
                world.entities.remove(self)
                return True

        else:
            self.health -= damage
    def despawn(self):
        if(self.origin[0]):
            world.toBeKilled.append(self)
            self.origin[0].tiles[self.origin[1][0]][self.origin[1][1]]=self.origin[2]
        else:
            print("couldnt despawn: no origin")
class Player(Entity):
    sidleImage = loadImage("player/player3.png")
    idleImage = loadImage("player/player.png")
    shoot1Image = loadImage("player/shooting.png")
    shoot2Image = loadImage("player/shooting2.png")
    def __init__(self, pos):
        super().__init__(pos,(None,(0,0),0))
        self.speed = 2
        self.image = Player.idleImage
        self.vehicle = None
        self.state = "walking"
        self.health = 20
        self.gun = True
        self.ammo = 10
        self.max_health = 20

    def update(self):
        pressed = pygame.key.get_pressed()
        if self.vehicle==None:
            if self.state == "tumbling":
                self.health -= speed
                self.vel *= 0.99
                self.image = Player.sidleImage
                self.angle = random.random()*np.pi*2
            elif self.state == "walking":

                self.image = Player.idleImage
                self.move(pressed)

                
                if(pressed[pygame.K_e]):
                    self.state="eating"
                    self.stateTimer=0
                elif(pressed[pygame.K_LSHIFT] and not self.shiftDown):
                    self.shiftDown = True
                    self.enterClosestVehicle()
                #shooting logic
                elif pygame.mouse.get_pressed()[0] and self.state == "walking" and self.gun == True and self.ammo>0:
                    mouse_screen_pos = pygame.mouse.get_pos()
                    relative_mouse_x = mouse_screen_pos[0] - screenWidth//2
                    relative_mouse_y = mouse_screen_pos[1] - screenHeight//2
                    self.angle = np.arctan2(relative_mouse_y, relative_mouse_x)
                    self.image = Player.shoot2Image
                    self.stateTimer = 0
                    self.state = "shooting"
                    self.ammo -= 1
                    self.vel = np.array((0.,0.))
                    for entity in world.entities:
                        relative_entity_pos = entity.pos - self.pos
                        # bullets are rays
                        # use projection formula to find closest point on bullet ray (ie projected point)
                        dot_product = max(0, relative_entity_pos[0]*relative_mouse_x + relative_entity_pos[1]*relative_mouse_y) #dont shoot backwards
                        relative_projected_point = np.array((relative_mouse_x, relative_mouse_y)) * dot_product / (relative_mouse_x**2 + relative_mouse_y**2)
                        projected_point = self.pos + relative_projected_point
                        distance_to_bullet_2 = (projected_point[0]-entity.pos[0])**2 + (projected_point[1]-entity.pos[1])**2
                        if distance_to_bullet_2 < entity.size**2:
                            entity.hurt(5)
                            distance_to_player = np.linalg.norm(relative_projected_point)
                            entity.vel += relative_projected_point/distance_to_player * 1000 / (distance_to_player+10)
                            print("yay")

            elif self.state == "eating":
                self.stateTimer+=1
                self.vel *= 0.8
                if(self.stateTimer>10):
                    self.eatClosest()
                if(not pressed[pygame.K_e]):
                    self.state="walking"

            elif self.state == "shooting":
                self.image = Player.shoot1Image
                self.stateTimer += 1
                if self.stateTimer > 20:
                    self.state = "walking"

            self.pos += self.vel
        else:
            self.state = "driving"
            self.vehicle.move(pressed)
            self.pos = self.vehicle.pos*1 # dont remove *1! acts as copying array!!!
            self.vel = self.vehicle.vel/2
            self.angle = self.vehicle.angle

            if(pressed[pygame.K_LSHIFT] and not self.shiftDown):
                self.shiftDown = True
                self.exitVehicle()


        if(not pressed[pygame.K_LSHIFT]):
            self.shiftDown = False


        playerChunk = world.getChunk(self.pos)
        if(playerChunk):
            if(playerChunk != world.centerChunk):
                world.centerChunk = playerChunk
                world.loadChunks()
        # no torus warping?

    def move(self, pressed):
        speed = self.speed
        direction = np.array([0.0,0.0])
        if(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]):
            direction+=np.array([1.0,0.0])
        if(pressed[pygame.K_a] or pressed[pygame.K_LEFT]):
            direction+=np.array([-1.0,0.0])
        if(pressed[pygame.K_s] or pressed[pygame.K_DOWN]):
            direction+=np.array([0.0,1.0])
        if(pressed[pygame.K_w] or pressed[pygame.K_UP]):
            direction+=np.array([0.0,-1.0])
        hyp = np.linalg.norm(direction)
        if hyp > 0:
            direction = speed * direction / hyp
            #cameraAngle = world.camera.angle
            #R = np.array([[np.cos(cameraAngle), -np.sin(cameraAngle)],
            #            [np.sin(cameraAngle),  np.cos(cameraAngle)]])
            #direction = R@direction
            self.angle = np.arctan2(direction[1], direction[0])

        self.vel = direction
    def eatClosest(self):
        bestDist = 50
        bestFood = None
        for entity in world.entities:
            if(isinstance(entity, Enemy)):
                dist = np.linalg.norm(entity.pos - self.pos)
                if dist < bestDist:
                    bestDist = dist
                    bestFood = entity

        # enter
        if bestFood:
            eatingspeed=0.05
            self.health=min(self.max_health,self.health+eatingspeed)
            bestFood.hurt(eatingspeed)
    def enterClosestVehicle(self):#, vehicle):
        # find closest enemy to eat
        bestDist = 50
        bestVehicle = None
        self.state = "driving"
        for entity in world.entities:
            if(isinstance(entity, Vehicle)):
                dist = np.linalg.norm(entity.pos - self.pos)
                if dist < bestDist:
                    bestDist = dist
                    bestVehicle = entity

        # enter
        if bestVehicle:
            self.vehicle = bestVehicle

    def exitVehicle(self):
        self.vehicle = None
        speed = np.linalg.norm(self.vel)
        if speed>3:
            self.state = "tumbling"
        else:
            self.state = "walking"
       
    def draw(self):
        if(not self.vehicle):
            world.camera.blitImage(gameDisplay, self.image, self.pos, np.array([32.0,32.0]), self.angle)
            #gameDisplay.blit(self.image,self.pos+np.array([-32.0,-32.0])) #-gridSize*self.size
            
        else:
            pass#pygame.draw.rect(gameDisplay, empty_color, (screenWidth//2-bar_width//2, bar_height*3, bar_width, bar_height), 0)
            #pygame.draw.rect(gameDisplay, health_color, (screenWidth//2-bar_width//2, bar_height, bar_width*self.health/max_health, bar_height), 0)

        bar_width = 500
        bar_height = 10
        health_color = (200,0,0)
        empty_color = (20,0,0)
        pygame.draw.rect(gameDisplay, empty_color, (screenWidth//2-bar_width//2, bar_height, bar_width, bar_height), 0)
        pygame.draw.rect(gameDisplay, health_color, (screenWidth//2-bar_width//2, bar_height, bar_width*self.health/self.max_health, bar_height), 0)
    
class Enemy(Entity): # or creature rather

    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.vehicle = None
        self.friction = 0.9
        self.state = 0
        self.stateTimer = 0

    def update(self):
        self.move()
        self.pos += self.vel
        self.vel *= self.friction

        # inbounds
        #self.pos=world.setInbounds(self.pos)

    def move(self):
        pass
        
class Box(Entity):
    idleImage = loadImage("things/box.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Box.idleImage
        self.size = 8
        self.health = 3
        self.friction = 0.9

    def update(self):
        super().update()
        self.vel *= self.friction
class Bush(Entity):
    idleImage = loadImage("things/bush.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Bush.idleImage
        self.size = 8
        self.health = 2
        self.friction = 0.9

    def update(self):
        super().update()
        self.vel *= self.friction

class Beetle(Enemy):
    idleImages = [loadImage("things/beetle/beetle1.png"),loadImage("things/beetle/beetle2.png")]
    biteImages = [loadImage("things/beetle/bite1.png"),loadImage("things/beetle/bite2.png")]
    deadImage = loadImage("things/beetle/dead.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Beetle.idleImages[0]
        self.size = 16
        self.health = 12

    def move(self):
        """
        direction = world.player.pos - self.pos
        self.vel = direction/np.linalg.norm(direction)
        self.angle = np.arctan2(direction[1], direction[0])
        """
        if self.health < 4:
            self.state = "dead"
            self.image = Beetle.deadImage

        if self.state == 0:

            self.angle += random.random()*0.2 - 0.1
            self.vel += np.array([np.cos(self.angle),np.sin(self.angle)]) * 0.1
            self.vel *= 0.9
            self.image = Beetle.idleImages[random.randint(0,1)]

            if random.random()<0.02:
                self.target = random.choice(world.entities)
                if random.random()<0.5:
                    self.target = (world.player)
                if not self.target == self:
                    dPos = self.target.pos - self.pos
                    hyp = np.linalg.norm(dPos)
                    if hyp<300:
                        self.state = 1 # attack
                        self.stateTimer = 0

        elif self.state == 1:
            if not self.target in world.entities+[world.player]:
                self.state = 0
                self.target = None
            else:
                dPos = self.target.pos - self.pos
                hyp = np.linalg.norm(dPos)
                if hyp < 40:
                    self.state = 2
                    self.stateTimer = 0
                else:
                    if hyp>0:
                        self.vel += dPos/hyp * 0.2
                    self.vel *= 0.9
                    self.angle = np.arctan2(self.vel[1],self.vel[0])
                    self.image = Beetle.idleImages[random.randint(0,1)]
                    if hyp>300:
                        self.state = 0

        elif self.state == 2:
            self.stateTimer += 1

            if self.stateTimer < 20:
                self.image = self.biteImages[0]
            elif self.stateTimer == 20:
                if self.target:
                    dPos = self.target.pos - self.pos
                    hyp = np.linalg.norm(dPos)
                    if hyp < 40:
                        self.target.hurt(4)
            elif self.stateTimer < 60:
                self.image = self.biteImages[1]
            else:
                self.state = 1
class Worm(Enemy):
    idleImages = [loadImage("things/worm/worm.png"),loadImage("things/worm/worm2.png")]
    biteImages = [loadImage("things/worm/bite1.png"),loadImage("things/worm/bite2.png")]
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Worm.idleImages[0]
        self.size = 12
        self.health = 5

    def move(self):
        """
        direction = world.player.pos - self.pos
        self.vel = direction/np.linalg.norm(direction)
        self.angle = np.arctan2(direction[1], direction[0])
        """
        self.stateTimer += 1
        if self.state == 0:

            self.angle += random.random()*0.2 - 0.1
            self.vel += np.array([np.cos(self.angle),np.sin(self.angle)]) * 0.1
            self.vel *= 0.9
            self.image = Worm.idleImages[self.stateTimer%32 < 16]

            if random.random()<0.03:
                self.target = random.choice(world.entities)
                if not self.target == self:
                    dPos = self.target.pos - self.pos
                    hyp = np.linalg.norm(dPos)
                    if hyp<400:
                        self.state = 1 # attack
                        self.stateTimer = 0

        elif self.state == 1:
            if not self.target in world.entities:
                self.state = 0
                self.target = None
            else:
                dPos = self.target.pos - self.pos
                hyp = np.linalg.norm(dPos)
                if hyp < 50:
                    self.state = 2
                    self.stateTimer = 0
                else:
                    if hyp>0:
                        self.vel += dPos/hyp * 0.3
                    self.vel *= 0.9
                    self.angle = np.arctan2(self.vel[1],self.vel[0])
                    self.image = Worm.idleImages[self.stateTimer%16 < 8]
                    if hyp>500:
                        self.state = 0

        elif self.state == 2:

            if self.stateTimer < 10:
                self.image = self.biteImages[0]
            elif self.stateTimer == 10:
                if self.target:
                    self.target.hurt(2)
            elif self.stateTimer < 45:
                self.image = self.biteImages[1]
            else:
                if random.random()<0.5:
                    self.target = None
                self.state = 1

class Vehicle(Entity):
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.health = 20
        self.topspeed = 5.0
        self.acc = 0.1
        self.sideFriction = 0.95
        self.forwardFriction = 0.99
        self.braking = 0.9
        self.brakestop = 0.1
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
            self.vel = forwardVel + sideVel
            """
            speedRemainder=max(tot-self.traction,0)
            traction=tot-speedRemainder
            traction = traction*self.direction()
            remainder= self.vel*speedRemainder/tot
            self.vel=traction+remainder
            """

        for i in world.entities: #collidibles ?
            if i != self:
                if np.linalg.norm(self.pos - i.pos)<self.size + i.size:
                    self.collide(i)

        # inbounds
        #self.pos=world.setInbounds(self.pos)

    def collide(self, other):
        speed = np.linalg.norm(self.vel)
        #if(isinstance(other,Vehicle)):
        other.vel+=self.vel
        otherHealthBefore = other.health
        attackDamage = speed*self.size/16 #mass?
        killed = other.hurt(attackDamage)
        if killed:
            self.vel *= 1 - otherHealthBefore / attackDamage
        else:
            self.vel = -0.1 * self.vel


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
        forwardVel = (np.dot(self.vel,self.direction()))*self.braking
        #tot=self.totalSpeed()
        self.angle+=direction*self.handling*forwardVel/self.topspeed#min(self.turnTraction,

    def totalSpeed(self):
        return np.linalg.norm(self.vel)

    def brake(self):
        forwardVel = (np.dot(self.vel,self.direction()))*self.braking
        sideVel = (np.dot(self.vel,self.direction(np.pi/2)))*1
        tot=self.totalSpeed()
        if forwardVel > 0.1 and -0.1 < sideVel < 0.1: # sidevel så att man inte backar när man driftar med broms men märks typ inte ens.
            if(tot!=0):
                if(forwardVel<self.brakestop):
                    forwardVel=0
                else:
                    forwardVel-=self.brakestop/2
                self.vel = self.direction()*forwardVel + self.direction(np.pi/2)*sideVel
        else:
            self.vel*=self.braking
            self.vel-=self.acc*self.direction()
    
    def accelerate(self):
        if(self.totalSpeed()<self.topspeed):
            self.vel+=self.acc*self.direction()

class RaceCar(Vehicle):
    idleImage = loadImage("vehicles/car.png")
    def __init__(self,pos,origin):
        super().__init__(pos,origin)
        self.image = RaceCar.idleImage

        self.topspeed = 6.0
        self.acc = 0.1
        self.sideFriction = 0.95
        self.forwardFriction = 0.98
        self.braking = 0.95
        self.handling = 0.05
class SlowCar(Vehicle):
    idleImage = loadImage("vehicles/car2.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = SlowCar.idleImage

        self.topspeed = 3.5
        self.acc = 0.05
        self.sideFriction = 0.9
        self.forwardFriction = 0.99
        self.braking = 0.95
        self.handling = 0.03

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