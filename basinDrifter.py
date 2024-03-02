import pygame
import random
import time
import os
import math
import numpy as np
import noise
from PIL import Image


# tiles
# health bar
# combat
# items
# inventory

# lighting?
#inside houses?


#enemies with different behaviour, fågel, ko, Carnivour and herbiovre, berry bushes and behaviour change
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

def crIntersect(circlepos, radius, rectcenter,width,height):
    circleDistance = np.abs(circlepos-rectcenter)

    if (circleDistance[0] > (width/2 + radius)):
        return False
    if (circleDistance[1] > (height/2 + radius)):
        return False

    return True
    if (circleDistance[0] <= (width/2)):
        return True
    if (circleDistance[1] <= (height/2)):
        return True

    cornerDistance_sq = (circleDistance[0] - width/2)**2+(circleDistance[1] - height/2)**2
    return cornerDistance_sq <= (radius**2)

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
        if image == None:
            raise Exception("Drawing with image==None")

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

    def get_screen_pos(self,pos):
        return np.array([screenWidth//2, screenHeight//2]) + (pos - self.pos)

class UI():

    gunImage = loadImage("UI/gun.png")
    bulletImage = loadImage("UI/bullet.png", 32)
    bombImage = loadImage("UI/bomb.png")

    @classmethod
    def draw(cls, game):
        # GUN
        gameDisplay.blit(cls.gunImage, (0,screenHeight-100))
        for i in range(game.player.ammo):
            gameDisplay.blit(cls.bulletImage, (30+10*i,screenHeight-60))
        # BOMBS
        for i in range(game.player.bombs):
            gameDisplay.blit(cls.bombImage, (-10+ 10*i,screenHeight-150))

        # HEALTH
        bar_width = 500
        bar_height = 10
        health_color = (200,0,0)
        empty_color = (20,0,0)
        pygame.draw.rect(gameDisplay, empty_color, (screenWidth//2-bar_width//2, bar_height, bar_width, bar_height), 0)
        pygame.draw.rect(gameDisplay, health_color, (screenWidth//2-bar_width//2, bar_height, bar_width*world.player.health/world.player.max_health, bar_height), 0)

        if world.player.vehicle:
            bar_width = 200
            bar_height = 5
            health_color = (100,100,0)
            empty_color = (10,10,0)
            pygame.draw.rect(gameDisplay, empty_color, (screenWidth//2-bar_width//2, 30, bar_width, bar_height), 0)
            pygame.draw.rect(gameDisplay, health_color, (screenWidth//2-bar_width//2, 30, bar_width*world.player.vehicle.fuel/world.player.vehicle.maxfuel, bar_height), 0)





class World():
    #groundSize = 448
    worldsize = 100 #chunks x chunks
    chunksize = 14 #tiles x tiles #14*32 = 448 och 448 är stort nog för att man inte ska se world border (laggar om den är större?)
    tilesize = 32 #pixels x pixels
    groundSize = chunksize*tilesize #448
    def __init__(self):
        self.player=None
        self.chunks = []#[[Chunk(random.randint(1,100000),np.array([i,j])) for i in range(self.worldsize)] for j in range(self.worldsize)]
        self.entities = []
        self.effects = []
        self.camera = Camera()
        self.size = 1300.0
        self.centerChunk = None
        self.loadedChunks = []
        self.toBeKilled = [] # what is this ? ?!???

        #self.surf = pygame.Surface((self.groundSize*4,self.groundSize*4)).convert_alpha()
        #for x in [0,1,2,3]:
        #    for y in [0,1,2,3]:
        #        self.surf.blit(self.groundImage,np.array([x*self.groundSize,y*self.groundSize]))
    def getTarget(self,pos,distance=None,condition=lambda x:True,includePlayer=True,extraPlayerChance=0,closest=False):
        targets=self.entities+[world.player]*includePlayer
        #filter according to range
        targets = filter(lambda x:np.linalg.norm(x.pos-pos)<distance,targets)
        targets = filter(lambda x:x.visible,targets)
        targets = list(filter(condition,targets))
        target = None
        if(targets):
            if(closest):
                bestDist = distance
                for possible in targets:
                    dist = np.linalg.norm(possible.pos - pos)
                    if dist < bestDist:
                        bestDist = dist
                        target = possible
            else:
                target = random.choice(targets)

        if(random.random()<extraPlayerChance and world.player.visible):
            target = world.player
        return target
    def generateWorld(self):
        SEED = random.random()*100
        scale = 0.02
        self.chunks = [[0 for i in range(self.worldsize)] for j in range(self.worldsize)]
        for x in range(World.worldsize):
            for y in range(World.worldsize):
                biome = 1*(noise.pnoise2(SEED+x * scale,SEED+y * scale, octaves=9, persistence=0.5, lacunarity=3)>0)

                self.chunks[y][x]=Chunk(random.randint(1,100000),np.array([x,y]),biome)

        self.makeRoads()
        center=np.array([self.groundSize*self.worldsize//2,self.groundSize*self.worldsize//2]).astype("float64")
        self.centerChunk = self.getChunk(center)
        if __name__ == '__main__':
            self.player = Player(center)
            
            self.loadChunks()
    def makeRoads(self):
        #for r in range(self.worldsize//3):
        def inbounds(p):
            if(p[0]>=0 and p[0]<self.worldsize and p[1]>=0 and p[1]<self.worldsize):
                return True
            return False
        North=np.array([0,-1])
        South=np.array([0,1])
        East=np.array([1,0])
        West=np.array([-1,0])
        
        for i in range(30):
            startpoint = np.array([random.randint(3,self.chunksize-4),random.randint(3,self.chunksize-4)])
            pos = [random.randint(0,self.worldsize-1),random.randint(0,self.worldsize-1)]
            self.chunks[pos[1]][pos[0]].ends+=1
            moving = random.choice([North,West,East,South])
            for i in range(random.randint(80,100)):
                if(random.random()>0.7):
                    moving = random.choice([n for n in [North,West,East,South] if not (np.array_equal(n,-moving))])
                while(not inbounds(pos+moving)):
                    moving = random.choice([n for n in [North,West,East,South] if not (np.array_equal(n,-moving))])
                #make endpoint np.array based on randomness and moving direction
                endpoint = random.randint(3,self.chunksize-4)*np.flip(abs(moving))+(self.chunksize-1)*(moving+abs(moving))//2
                #print(startpoint,endpoint,pos)

                self.chunks[pos[1]][pos[0]].roads.append([startpoint,endpoint])
                startpoint = endpoint-moving*(self.chunksize-1)
                pos = pos+moving
            self.chunks[pos[1]][pos[0]].ends+=1
    def loadChunks(self):
        x=self.centerChunk.gridpos[1]
        y=self.centerChunk.gridpos[0]
        #print(x,y)
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
        for entity in self.toBeKilled: # kill stuff when loading chunks? why?!
            if entity in self.entities:
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
            return self.chunks[y][x] 
    def getTile(self,pos):
        return self.getChunk(pos).getTile(pos) # tile type        
    def update(self):
        self.player.update()
        for entity in self.entities:
            entity.update()
        for effect in self.effects:
            effect.update()

        self.camera.update()
    def tileCollision(self,pos,radius):
        #get all possible tiles
        tiles=[]
        n = radius//self.tilesize + 1
        for x in range(-n,n+1):
            for y in range(-n,n+1):
                offsetpos=pos+np.array([x*self.tilesize,y*self.tilesize])
                chunk = world.getChunk(offsetpos)
                if chunk and chunk.tiles: 
                    tiles.append((chunk.getTilePosfromPos(offsetpos),self.getTile(offsetpos)))
        for tile in tiles:
            if(tile[1]>200):        
                if(crIntersect(pos, radius, tile[0],self.tilesize,self.tilesize)):
                    return True
        
        return False


    def draw(self):
        
        
         #       self.groundSize*((self.player.pos)//self.groundSize)
        #world.camera.blitImage(gameDisplay, self.surf, self.groundSize*((self.player.pos+self.groundSize//2)//self.groundSize), (self.groundSize*2, self.groundSize*2), 0)
        for chunk in world.loadedChunks:
            chunk.draw()
        for entity in self.entities:
            entity.draw()
        for effect in self.effects:
            effect.draw()
        self.player.draw()
        UI.draw(self)
    def setInbounds(self,pos):
        x=pos[0]
        y=pos[1]
        if(x>self.player.pos[0]+self.size/2): 
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
    sandImage=loadImage("tiles/sand.png",size=World.groundSize)
    roadImage=loadImage("tiles/roadc.png",size=World.tilesize).convert()
    wallImage=loadImage("tiles/wall.png",size=World.tilesize)
    def __init__(self, seed,gridpos,chunktype):
        self.seed=seed
        self.tiles=None
        self.visited=False
        self.gridpos = gridpos
        self.pos = World.groundSize*self.gridpos.astype("float64")
        self.chunktype=chunktype
        if(self.chunktype%2==0):
            self.image = self.groundImage
        else:
            self.image = self.sandImage
        self.roads=[]
        #to determine which tiles to make interesting
        self.ends = 0

        #self.toBeKilled = []  # remove this? /b
    def generateTiles(self):
        random.seed(self.seed)
        self.tiles=[[0 for i in range(World.chunksize)] for j in range(World.chunksize)] #easy spatial lookup but slow iteration?
        if random.random()<0.4:
            for i in range(random.randint(4,10)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 5 # bush
        elif random.random()<0.3:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 2 # beetle
        elif random.random()<0.4:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 6 # worm
        elif random.random()<0.4:
            for i in range(random.randint(6,9)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 8 # armadillo
        elif random.random()<0.2:
            for i in range(random.randint(1,2)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 7 # dragonfly
        elif random.random()<0.1:
            for i in range(random.randint(2,5)):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 1 # box
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 201 # wall
                
        else:
            for i in range(random.randint(0,random.randint(0,1))):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 3 # slow car
            for i in range(random.randint(0,random.randint(0,1))):
                self.tiles[random.randint(0,World.chunksize-1)][random.randint(0,World.chunksize-1)] = 4 # race car
        
        for road in self.roads:
            self.makeRoad(road[0],road[1])

        if (self.gridpos[0] == world.worldsize//2 and self.gridpos[1] == world.worldsize//2):
            startOfGameChunk = True
        else:
            startOfGameChunk = False
        if(self.ends>0) or startOfGameChunk:
            if startOfGameChunk:
                structure_name = "starting_house"
                self.tiles[0][7]=3
            else:
                structure_name = random.choice(["structure_groove","structure_house","structure_hut"])
            img = Image.open("assets/textures/blueprints/"+structure_name+".png")
            img.load()
            data = np.asarray( img, dtype="int32" )
            if(random.random()<0.5):
                data = np.fliplr(data)
            for i in range(random.randint(0,3)):
                data = np.rot90(data)
            randomizedEnemyType = random.choice([2,6,7,8])
            for x in range(world.chunksize):
                for y in range(world.chunksize):
                    color = data[x][y]
                    if(np.array_equal(color,np.array([0,0,0,255]))):

                        self.tiles[y][x]=201
                    if(np.array_equal(color,np.array([0,255,0,255]))):
                        if(random.random()<0.5):
                            self.tiles[y][x]=random.choice([1]) #bombs? ammo? fuel dunks?

                    if(np.array_equal(color,np.array([255,0,0,255]))):
                        if(random.random()<0.5):
                            self.tiles[y][x]=randomizedEnemyType

        self.visited=True
    def makeRoad(self,start,end):
        roadsize=3
        for x in range(World.chunksize): #scipy.sparse find? onödig optimisering
            for y in range(World.chunksize):
                tilePos=np.array([x,y])
                t=min(1,max(0,np.dot((end-start),tilePos-start)/(np.linalg.norm(end-start)**2)))
                projected=start+(end-start)*t              
                d=np.linalg.norm(projected-tilePos)
                if d < roadsize:
                    self.tiles[x][y]=101 

    def inbounds(self,pos):
        if(pos[0]>=self.pos[0] and pos[1]>=self.pos[1] and pos[0]<self.pos[0]+world.groundSize and pos[1]<self.pos[1]+world.groundSize):
            return True
        else:
            return False
    def getTile(self,pos):
        x=int((pos[0]-self.pos[0])//World.tilesize) #necessary beacuse of numpy?
        #print(pos,x)
        y=int((pos[1]-self.pos[1])//World.tilesize)
        #print(x,y)
        return self.tiles[x][y] 

    def getTilePos(self,x,y):
        return self.pos+np.array([x*World.tilesize,y*World.tilesize]) # local chunk coordinate -> global pos
    def getTilePosfromPos(self,pos):
        x=int((pos[0]-self.pos[0])//World.tilesize)
        y=int((pos[1]-self.pos[1])//World.tilesize)
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
                elif(tile==7): #Dragonfly
                    world.entities.append(Dragonfly(pos,origin))
                elif(tile==8): #Armadillo
                    world.entities.append(Armadillo(pos,origin))

                if(tile<100): #tile numbers under 100 are entities, over 100 are other types of tiles
                    self.tiles[x][y]=0

                #101 road

                #>200 collible
    def load(self):
        if(not self.visited):
            self.generateTiles()
        self.generateEntities()

    def draw(self):
        world.camera.blitImage(gameDisplay, self.image, self.pos+np.array([World.groundSize-0.5*World.tilesize,World.groundSize-0.5*World.tilesize]), (World.groundSize,World.groundSize), 0)
        for x in range(World.chunksize): #scipy.sparse find? onödig optimisering
            for y in range(World.chunksize):
                tile=self.tiles[x][y]
                if(tile==101):
                    world.camera.blitImage(gameDisplay, self.roadImage, self.pos+np.array([x,y])*World.tilesize, (World.tilesize//2,World.tilesize//2), 0)
                if(tile==201):
                    world.camera.blitImage(gameDisplay, self.wallImage, self.pos+np.array([x,y])*World.tilesize, (World.tilesize//2,World.tilesize//2), 0)

        pygame.draw.line(gameDisplay,(0,0,0),world.camera.get_screen_pos(self.pos+np.array([-0.5,-0.5])*World.tilesize),world.camera.get_screen_pos((self.pos+np.array([-0.5,13.5])*World.tilesize)),3)
        pygame.draw.line(gameDisplay,(0,0,0),world.camera.get_screen_pos(self.pos+np.array([-0.5,-0.5])*World.tilesize),world.camera.get_screen_pos((self.pos+np.array([13.5,-.5])*World.tilesize)),3)
    



class Entity():
    imageSize = gridSize
    
    def __init__(self, pos,origin):
        self.origin=origin
        self.pos = pos*1 # VERY IMPORTANT *1
        self.angle = 0.
        self.vel = np.array([0.0,0.0])
        self.size = 16 
        self.image = None
        self.health = 10
        self.visible = True
        self.state = "unknown"
    def update(self):
        #print(self, self.pos, self.vel)
        self.pos += self.vel
        if(world.tileCollision(self.pos,self.size) and np.linalg.norm(self.vel)>0):
            self.pos-=self.vel
            sideComponent = np.dot(self.vel,np.array([[0,-1],[1,0]]))/np.linalg.norm(self.vel) # rotational matrix (90 degrees) 

            self.vel = -0.1 * self.vel + (random.random()-0.5)*sideComponent*3
    def draw(self): 
        #print("in entity:", self, self.image)
        pygame.draw.circle(gameDisplay,(255,0,0),world.camera.get_screen_pos(self.pos),self.size)
        if(isinstance(self,Enemy)):
            pygame.draw.line(gameDisplay,(0,0,0),world.camera.get_screen_pos(self.pos)+np.array([-20,-40]),world.camera.get_screen_pos(self.pos)+np.array([20,-40]),4)
            hplength=max(0,40*(self.health/(self.max_health/2)-1))
            if(hplength):
                pygame.draw.line(gameDisplay,(255,0,0),world.camera.get_screen_pos(self.pos)+np.array([-20,-40]),world.camera.get_screen_pos(self.pos)+np.array([-20+hplength,-40]),4)

        world.camera.blitImage(gameDisplay, self.image, self.pos, (self.imageSize//2,self.imageSize//2), self.angle)
        
        
    def hurt(self, damage):
        if damage >= self.health:
            self.health=0
            self.die()
        else:
            self.health -= damage
    def heal(self, damage):
        self.health=min(self.max_health, self.health+damage)
    def die(self):
        if self in world.entities:
            world.entities.remove(self)
    def despawn(self):
        if(self.origin[0]):
            world.toBeKilled.append(self)
            self.origin[0].tiles[self.origin[1][0]][self.origin[1][1]]=self.origin[2]
        else:
            print(self,"couldnt despawn: no origin")
class Player(Entity):
    sidleImage = loadImage("player/player3.png")
    idleImage = loadImage("player/player.png")
    shoot1Image = loadImage("player/shooting.png")
    shoot2Image = loadImage("player/shooting2.png")
    eat1Image = loadImage("player/eating.png")
    eat2Image = loadImage("player/eating2.png")
    punchImage = loadImage("player/punch.png")
    punch2Image = loadImage("player/punch2.png")
    def __init__(self, pos):
        super().__init__(pos,(None,(0,0),0)) # what is this hack!?
        self.speed = 0.4
        self.image = Player.idleImage
        self.vehicle = None
        self.state = "walking"
        self.stateTimer = 0
        self.health = 20
        self.max_health = 20
        self.gun = True
        self.ammo = 1
        self.bombs = 0
        self.fuelDunks = 0

    def update(self):
        pressed = pygame.key.get_pressed()
        if self.vehicle==None:
            self.stateTimer += 1
            if self.state == "tumbling":
                self.health = max(0, self.health-np.linalg.norm(self.vel)*0.01)
                self.vel *= 0.98
                self.image = Player.sidleImage
                self.angle = random.random()*np.pi*2
                if np.linalg.norm(self.vel)<2:
                    self.state = "walking"
            elif self.state == "walking":

                self.image = Player.idleImage
                self.move(pressed)

                
                if(pressed[pygame.K_e]):
                    self.state = "eating"
                    self.stateTimer = 0
                elif(pressed[pygame.K_SPACE] and not self.shiftDown):
                    self.punch()
                elif(pressed[pygame.K_LSHIFT] and not self.shiftDown):
                    self.shiftDown = True
                    self.enterClosestVehicle()
                elif(pressed[pygame.K_q] and not self.qDown):
                    self.qDown = True
                    self.throwBomb()
                elif(pressed[pygame.K_f] and not self.fDown):
                    self.fDown = True
                    self.refuelVehicle()
                #shooting logic
                elif pygame.mouse.get_pressed()[0] and self.state == "walking" and self.gun == True:
                    self.shoot()

            elif self.state == "eating":
                self.image = [Player.eat1Image,Player.eat2Image][(self.stateTimer//20)%2]
                self.vel *= 0.8
                if(self.stateTimer>10):
                    self.eatClosest()
                if(not pressed[pygame.K_e]):
                    self.state="walking"

            elif self.state == "shooting":
                self.image = Player.shoot1Image
                if self.stateTimer > 20:
                    self.state = "walking"

            elif self.state == "punching":
                
                if self.stateTimer==10:
                    facingOffset = np.array([np.cos(self.angle),np.sin(self.angle)])
                    self.vel = facingOffset * 2
                if self.stateTimer==15:
                    facingOffset = np.array([np.cos(self.angle),np.sin(self.angle)])
                    for entity in world.entities:
                        dist = np.linalg.norm(entity.pos - (self.pos+facingOffset*20) )
                        if dist<20+entity.size:
                            entity.hurt(2)
                            entity.vel += facingOffset * 4
                            print("punched a ",entity)
                            #self.hurt(0.1)
                if self.stateTimer < 10:
                    self.image = self.punchImage
                elif self.stateTimer<30:
                    self.image = self.punch2Image
                    self.vel *= 0.8

                elif self.stateTimer<40:
                    self.image = self.punchImage
                else:
                    self.state = "walking"

            else:
                print("UNKNOWN PLAYER STATE: ", self.state)

            self.pos += self.vel
            if(world.tileCollision(self.pos,self.size)):
                self.pos-=self.vel
                sideComponent = np.dot(self.vel,np.array([[0,-1],[1,0]]))/np.linalg.norm(self.vel) # rotational matrix (90 degrees) 
                self.vel = -0.1 * self.vel + (random.random()-0.5)*sideComponent*3 
        else:
            self.state = "driving"
            self.vehicle.move(pressed)
            self.pos = self.vehicle.pos*1 # dont remove *1! acts as copying array!!!
            self.vel = self.vehicle.vel
            self.angle = self.vehicle.angle

            if(pressed[pygame.K_LSHIFT] and not self.shiftDown):
                self.shiftDown = True
                self.exitVehicle()


        if(not pressed[pygame.K_LSHIFT]):
            self.shiftDown = False
        if(not pressed[pygame.K_q]):
            self.qDown = False
        if(not pressed[pygame.K_f]):
            self.fDown = False


        playerChunk = world.getChunk(self.pos)
        if(playerChunk):
            if(playerChunk != world.centerChunk):
                world.centerChunk = playerChunk
                world.loadChunks()
        # no torus warping?

    def move(self, pressed):
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
            direction = direction / hyp
            #cameraAngle = world.camera.angle
            #R = np.array([[np.cos(cameraAngle), -np.sin(cameraAngle)],
            #            [np.sin(cameraAngle),  np.cos(cameraAngle)]])
            #direction = R@direction
            self.angle = np.arctan2(direction[1], direction[0])

        self.vel += direction * (self.health/self.max_health) * self.speed
        self.vel *= 0.8


    def throwBomb(self):
        if self.bombs>0:
            self.bombs -= 1
            bomb = Bomb(self.pos)
            bomb.state = "fusing"
            world.entities.append(bomb)

    def shoot(self):
        if self.ammo>0:
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
                    print("you hit a shot at ",entity)
                    entity.hurt(5)
                    distance_to_player = np.linalg.norm(relative_projected_point)
                    if distance_to_player>0:
                        entity.vel += relative_projected_point/(distance_to_player) * 10#00 / (distance_to_player+10)

    def punch(self):
        self.state = "punching"
        self.stateTimer = 0
        #self.angle = np.arctan2(relative_mouse_y, relative_mouse_x)
        

    def eatClosest(self):
        bestFood = world.getTarget(self.pos,distance=50,condition=lambda x:isinstance(x,Enemy),closest=True)
        # eat
        if bestFood:
            eatingspeed=0.02
            self.health=min(self.max_health,self.health+eatingspeed) # 100% lifesteaL!!?
            bestFood.hurt(eatingspeed)
    def refuelVehicle(self):
        if self.fuelDunks>0:
            bestVehicle = world.getTarget(self.pos,distance=50,condition=lambda x:isinstance(x,Vehicle),closest=True)
            if bestVehicle:
                bestVehicle.fuel = min(bestVehicle.maxfuel, bestVehicle.fuel + 3000)
                self.fuelDunks -= 1

    def enterClosestVehicle(self):
        # enter
        bestVehicle = world.getTarget(self.pos,distance=50,condition=lambda x:isinstance(x,Vehicle),closest=True)
        if bestVehicle:
            self.visible=False
            self.state = "driving"
            self.vehicle = bestVehicle
    def exitVehicle(self):
        self.vehicle = None
        self.visible = True
        speed = np.linalg.norm(self.vel)
        if speed>3:
            self.state = "tumbling"
        else:
            self.state = "walking"
       
    def draw(self):
        if(not self.vehicle):
            world.camera.blitImage(gameDisplay, self.image, self.pos, np.array([self.imageSize//2,self.imageSize//2]), self.angle)
            #gameDisplay.blit(self.image,self.pos+np.array([-32.0,-32.0])) #-gridSize*self.size
            
        else:
            pass#pygame.draw.rect(gameDisplay, empty_color, (screenWidth//2-bar_width//2, bar_height*3, bar_width, bar_height), 0)
            #pygame.draw.rect(gameDisplay, health_color, (screenWidth//2-bar_width//2, bar_height, bar_width*self.health/max_health, bar_height), 0)

class Bomb(Entity):
    
    idleImage = loadImage("things/bomb/bomb.png")
    fuseImages = [loadImage("things/bomb/livebomb1.png"), loadImage("things/bomb/livebomb2.png")]

    def __init__(self, pos):
        super().__init__(pos,(None,(0,0),0)) #"what is this hack!??"
        self.state = "idle"
        self.stateTimer = 0
        self.friction = 0.9
        self.health = 3
        self.size = 8
        self.fuse_time = 200

        self.image = self.idleImage

    def update(self):
        self.stateTimer += 1
        super().update()
        self.vel *= self.friction

        if self.state == "idle":
            self.image = self.idleImage
            player_dist = np.linalg.norm(self.pos - world.player.pos)
            #print(player_dist)
            # pickup
            if player_dist < 20 and world.player.state == "walking":
                world.entities.remove(self)
                world.player.bombs += 1

        elif self.state == "fusing":
            self.image = self.fuseImages[(self.stateTimer//10)%2]
            if self.stateTimer >= self.fuse_time+random.randint(1,100):
                self.explode()
        else:
            print(self.state)

    def die(self):
        print("i die -> explode")
        self.state = "fusing"
        self.stateTimer = self.fuse_time

    def explode(self):
        if self in world.entities:
            world.entities.remove(self)
        else:
            print("redundant removes?!? ( + redundant bomb explosions!!? )")
        self.stateTimer = 0

        blast_radius = 100

        for entity in world.entities+[world.player]:
            dPos = entity.pos - self.pos
            hyp = np.linalg.norm(dPos)

            if hyp < blast_radius:
                if hyp:
                    entity.vel = dPos/(hyp+1) * 10
                entity.hurt(10)
        world.effects.append(Explosion(self.pos))
class Fuel(Entity):
    
    idleImage = loadImage("things/fuel.png")

    def __init__(self, pos):
        super().__init__(pos,(None,(0,0),0)) #"what is this hack!??"
        self.state = "idle"
        #self.stateTimer = 0
        self.friction = 0.86
        self.health = 4
        self.timesExploded = 0 # for  debugging why everything explodes so many times

        self.image = self.idleImage

    def update(self):
        #self.stateTimer += 1
        super().update()
        self.vel *= self.friction

        if self.state == "idle":
            self.image = self.idleImage
            player_dist = np.linalg.norm(self.pos - world.player.pos)
            
            # pickup
            if player_dist < 20 and world.player.state == "walking":
                world.entities.remove(self)
                world.player.fuelDunks += 1
        else:
            print(" !!! unknown state in Fuel object:", self.state)

    def die(self):
        #print("fuel object dies -> explode")
        self.explode()

    def explode(self):
        self.timesExploded += 1
        if self.timesExploded >1:
            print("WTF",self.timesExploded,"TIMES EXPLODED")
        if self in world.entities:
            world.entities.remove(self)
        else:
            print("unnecessary removes of fuel object")
        self.stateTimer = 0

        blast_radius = 100

        for entity in world.entities+[world.player]:
            dPos = entity.pos - self.pos
            hyp = np.linalg.norm(dPos)

            if hyp < blast_radius:
                if hyp:
                    entity.vel = dPos/(hyp+1) * 5
                entity.hurt(8)
        world.effects.append(Explosion(self.pos))

class Explosion():
    imageSize = 128

    explosion1 = loadImage("effects/newexplosion1.png",size=imageSize)
    explosion2 = loadImage("effects/newexplosion2.png",size=imageSize)
    explosion3 = loadImage("effects/bigexplosion2.png",size=imageSize)
    def __init__(self, pos):
        self.stateTimer = 0
        self.pos = pos
        self.image = self.explosion1

    def update(self):
        if self.stateTimer<6:
            self.image = self.explosion1
        elif self.stateTimer<12:
            self.image = self.explosion2
        else:
            self.image = self.explosion3
        if self.stateTimer > 20:
            world.effects.remove(self)
        self.stateTimer += 1

    def draw(self): 
        #print("in entity:", self, self.image)
        world.camera.blitImage(gameDisplay, self.image, self.pos, (self.imageSize//2,self.imageSize//2), random.random())
class Bullet(Entity):
    imageSize = 32
    idleImage = loadImage("UI/bullet.png", imageSize)

    def __init__(self, pos):
        super().__init__(pos,(None,(0,0),0)) #"what is this hack!??"
        #self.state = "idle"
        #self.stateTimer = 0
        self.friction = 0.9
        self.health = 1
        self.image = self.idleImage
        #self.small = True


    def update(self):
        #self.stateTimer += 1
        super().update()
        self.vel *= self.friction

        if True:
            self.image = self.idleImage
            player_dist = np.linalg.norm(self.pos-world.player.pos)
            if player_dist < 20 and world.player.state == "walking":
                world.entities.remove(self)
                world.player.ammo += 1
    
class Enemy(Entity): # or creature rather

    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.vehicle = None # wut?
        self.friction = 0.85
        self.state = "unknown" #unknown, strolling approaching, searching_food
        self.stateTimer = 0
        self.target = None
        self.mood = "happy"
        self.senseRange = 500
        self.attackRange = 40
        self.speed = 0.2
        self.huntChance = 1
        self.threat = None
        self.isThreat = lambda x:(isinstance(x,Enemy) or isinstance(x,Player)) and not x==self and not x==self.target and not x.state=="dead"
    def hunger(self):
        if(random.random()<0.003 and not self.state == "dead"): 
            self.hurt(0.2)

    def update(self):
        
        self.hunger()
        self.deathCheck()
        self.stateMachine()
        self.move()
        #friction and collision
        self.vel *= self.friction
        super().update()
        # inbounds
    def deathCheck(self):
        if self.health < self.max_health/2:
            self.state = "dead"
            self.image = self.deadImage

    def stateMachine(self):
        self.stateTimer += 1
        if(self.state=="unknown"):
            self.forcedMoodBehaviour()
        elif(self.state=="strolling"):
            if random.random()<0.1:
                self.moodBehaviour()
        elif(self.state=="searching_food"):
            if(random.random()<self.huntChance):            
                self.target = self.findFood()
                if self.target:
                    if not self.target == self:
                        self.state = "approaching"
                        self.stateTimer = 0
            self.moodBehaviour()
        elif(self.state=="approaching"):
            if not self.target in world.entities+[world.player]: # more general maybe?
                self.target = None
                self.forcedMoodBehaviour()
            else:
                hyp = np.linalg.norm(self.target.pos - self.pos)
                if hyp < self.attackRange:
                    self.state = "attacking"
                    self.stateTimer = 0
                else:
                    if hyp>self.senseRange:
                        self.target = None
                        self.forcedMoodBehaviour()
            self.moodBehaviour()
        elif(self.state=="attacking"):
            self.attack()
        elif(self.state=="fleeing"):
            self.threat=self.findClosestThreat()
            self.moodBehaviour()

        #elif(self.state=="searching"):
    def forcedMoodBehaviour(self):
        newMood=self.checkMood()
        self.mood = newMood
        if(self.mood=="scared"):
            self.scaredBehaviour()
        elif(self.mood=="hungry"):
            self.hungryBehaviour()
        elif(self.mood=="happy"):
            self.happyBehaviour()
    def moodBehaviour(self):
        mood=self.mood
        newMood=self.checkMood()
        if(not mood==newMood):
            self.forcedMoodBehaviour()            
    def scaredBehaviour(self):
        self.threat=self.findClosestThreat()
        self.state="fleeing" #should flee instead
    def happyBehaviour(self):
        self.state="strolling"   
    def findFood(self):
        return world.getTarget(self.pos,distance=self.senseRange,includePlayer=False,extraPlayerChance=0,condition=lambda x:not x==self)
    def findClosestThreat(self):
        return world.getTarget(self.pos,distance=self.senseRange/4,includePlayer=True,condition=self.isThreat,closest=True)
    def hungryBehaviour(self):
        self.state = "searching_food"        
    def checkMood(self):
        mood="happy"
        if(self.health<self.max_health*0.95):
            mood="hungry"
        if(self.findClosestThreat()):
            mood="scared"
        # Add Afraid
        return mood
    def moveToTarget(self,speedFactor=2):
        self.moveToPos(self.target.pos,speedFactor=speedFactor)
    def moveFromThreat(self,speedFactor=2):
        self.moveFromPos(self.threat.pos,speedFactor=speedFactor)
    def moveToPos(self,pos,speedFactor=1):
        dPos = pos - self.pos
        hyp=np.linalg.norm(dPos)
        if hyp>0:
            self.vel += dPos/hyp * (self.health/(self.max_health/2)-1) * self.speed * speedFactor
        self.angle = np.arctan2(self.vel[1],self.vel[0])
    def moveFromPos(self,pos,speedFactor=1):
        dPos = pos - self.pos
        hyp=np.linalg.norm(dPos)
        if hyp>0:
            self.vel -= dPos/hyp * (self.health/(self.max_health/2)-1) * self.speed * speedFactor
        self.angle = np.arctan2(self.vel[1],self.vel[0])


    def move(self):
        if self.state=="strolling":
            self.strollingMove()
        elif self.state=="searching_food":
            self.searchMove()
        elif self.state=="approaching":
            self.moveToTarget()
        elif self.state=="fleeing":
            if(self.threat):
                self.moveFromThreat()
            else:
                print("why am i fleeing?", self)    
        elif self.state=="retreating": #Dragonfly specific
            self.moveToPos(self.nest,speedFactor=1) #movetohome?
        elif self.state=="rotating": #Dragonfly specific
            self.moveRotate()
        else:
            return
        # only animates if moved
        self.moveAnimation()
    def moveAnimation(self):
        pass
    def searchMove(self):
        self.strollingMove()
    def strollingMove(self):
        self.angle += random.random()*0.2 - 0.1
        self.vel += np.array([np.cos(self.angle),np.sin(self.angle)]) * (self.health/(self.max_health/2)-1) * self.speed


        
class Box(Entity):
    idleImage = loadImage("things/box.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Box.idleImage
        self.size = 20
        self.health = 3
        self.friction = 0.9

    def update(self):
        super().update()
        self.vel *= self.friction

    def die(self):
        super().die()
        k = random.randint(1,4)
        loots = random.choices([Bullet,Bomb,Fuel], weights = [5, 1, 1], k = k)
        for i in range(k):
            loot = loots[i](self.pos)
            loot.vel = np.array([random.uniform(-2,2),random.uniform(-2,2)])
            world.entities.append(loot)

class Bush(Entity):
    idleImage = loadImage("things/bush.png")
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Bush.idleImage
        self.size = 15
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
        self.speed = 0.2
        self.max_health = self.health
        self.isThreat = lambda x:(isinstance(x,Beetle) or isinstance(x,Dragonfly) or isinstance(x,Vehicle)) and not x==self and not x==self.target and not x.state=="dead"
    def moveAnimation(self):
        self.image = Beetle.idleImages[random.randint(0,1)]
    def findFood(self):
        return world.getTarget(self.pos,distance=self.senseRange,includePlayer=False,extraPlayerChance=0.5, condition=lambda x:(isinstance(x,Enemy) or isinstance(x,Player)) and not x==self)
    def attack(self):
        if self.stateTimer < 20: # prebite
            # face correctly
            self.moveToTarget()
            self.image = self.biteImages[0]
        elif self.stateTimer == 20: # bite
            if self.target:
                hyp = np.linalg.norm(self.target.pos - self.pos)
                if hyp < 40:
                    self.target.hurt(4)
                    self.heal(2)
                    # add hunger
        elif self.stateTimer < 60: # ending lag
            self.image = self.biteImages[1]
        else:
            self.state = "approaching"
class Worm(Enemy):
    idleImages = [loadImage("things/worm/worm.png"),loadImage("things/worm/worm2.png")]
    biteImages = [loadImage("things/worm/bite1.png"),loadImage("things/worm/bite2.png")]
    deadImage = loadImage("things/worm/dead.png")

    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Worm.idleImages[0]
        self.size = 13
        self.health = 5
        self.max_health = 5
        self.speed = 0.1
        self.senseRange = 400
        self.isThreat = lambda x:(isinstance(x,Enemy) or isinstance(x,Player) or isinstance(x,Vehicle)) and not x==self and not x==self.target and not x.state=="dead" and not isinstance(x,Worm)
    def findFood(self):
        return world.getTarget(self.pos,distance=self.senseRange,includePlayer=False,condition=lambda x:x.state=="dead" and not x==self)
    def moveAnimation(self):
        if(self.state=="strolling"):
            self.image = Worm.idleImages[self.stateTimer%32 < 16]
        if(self.state=="approaching" or self.state=="fleeing"):
            self.image = Worm.idleImages[self.stateTimer%16 < 8]

    def attack(self):
        if self.stateTimer < 10:
            self.image = self.biteImages[0]
        elif self.stateTimer == 10:
            if self.target:
                self.target.hurt(2)
                self.heal(1)
        elif self.stateTimer < 45:
            self.image = self.biteImages[1]
        else:
            if random.random()<0.5:
                self.target = None
                self.forcedMoodBehaviour()
            else:
                self.state = "approaching"
class Dragonfly(Enemy):
    idleImages = [loadImage("things/dragonfly/dragonfly.png",size=gridSize*2),loadImage("things/dragonfly/dragonflyL.png",size=gridSize*2),loadImage("things/dragonfly/dragonflyLR.png",size=gridSize*2),loadImage("things/dragonfly/dragonflyR.png",size=gridSize*2)]
    deadImage = loadImage("things/dragonfly/dead.png",size=gridSize*2)
    #biteImages = [loadImage("things/worm/bite1.png"),loadImage("things/worm/bite2.png")]
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = Dragonfly.idleImages[0]
        self.imageSize = gridSize*2
        self.size = 32
        self.health = 17
        self.max_health = 17
        self.grabbed = None
        self.nest = pos*1
        self.target = None
        self.senseRange = 800
        self.attackRange = 50
        self.speed = 0.3
        self.friction = 0.9
        self.isThreat = lambda x:(isinstance(x,Vehicle) or isinstance(x,Dragonfly)) and not x==self and not x==self.target and not x.state=="dead"
    def reset(self):
        self.forcedMoodBehaviour()
        self.stateTimer = 0
        self.grabbed = None
        self.target = None
    def moveRotate(self):
        if self.target and (not self.target==self):
            dPos=self.target.pos - self.pos
            self.angle = np.arctan2(dPos[1],dPos[0])
        else:
            self.angle += 0.02 
    def hungryBehaviour(self):
        self.state = "rotating"
    def happyBehaviour(self):
        self.state="rotating"    
    def stateMachine(self):
        super().stateMachine()

        if(self.state=="rotating"):
            if random.random()<0.01:
                if(self.mood=="happy"):
                    self.target = world.getTarget(self.pos,distance=self.senseRange,includePlayer=False,condition=lambda x:not isinstance(x,Enemy))
                elif(self.mood =="hungry"):
                    self.target = world.getTarget(self.pos,distance=self.senseRange,includePlayer=False,condition=lambda x:isinstance(x,Enemy),extraPlayerChance=0.05)
            
            if random.random()<0.01 and self.target:
                if not self.target == self:
                    self.state = "approaching"
                    self.stateTimer = 0
            self.moodBehaviour()

        
        elif(self.state=="retreating"):
            if np.linalg.norm(self.nest - self.pos) < self.attackRange/2: #close enough to nest   
                if(self.grabbed):
                    self.grabbed.hurt(1)
                    self.heal(1)
                self.reset()
            else:
                if(self.grabbed):
                    self.grabbed.pos=self.pos+self.vel*20 # maybe janky
                else:
                    self.reset()
    def moveAnimation(self):
        if(self.state=="approaching" or self.state=="fleeing"):
            self.image = Dragonfly.idleImages[(self.stateTimer%8)//2]
        elif(self.state=="retreating" or self.state=="rotating"):
            self.image = Dragonfly.idleImages[(self.stateTimer%32)//8]
    def attack(self):
        self.state = "retreating"
        self.stateTimer = 0
        self.grabbed = self.target     

class Armadillo(Enemy):
    idleImages = [loadImage("things/armadillo/armadillo1.png"),loadImage("things/armadillo/armadillo2.png")]
    biteImages = [loadImage("things/worm/bite1.png"),loadImage("things/worm/bite2.png")]
    deadImage = loadImage("things/armadillo/dead.png")

    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.image = self.idleImages[0]
        self.size = 16
        self.health = 10
        self.max_health = 10
        self.speed = 0.1
        self.senseRange = 400
        self.av = 0
        self.still = False
        self.stateTimer=random.randint(0,16)
        self.isThreat = lambda x:(isinstance(x,Enemy) or isinstance(x,Player) or isinstance(x,Vehicle)) and not x==self and not x==self.target and not isinstance(x,Armadillo) and not x.state=="dead"
    def findFood(self):
        return world.getTarget(self.pos,distance=self.senseRange,condition=lambda x:isinstance(x,Bush))
    def moveAnimation(self):
            self.image = self.idleImages[self.stateTimer%32 < 16]
    def strollingMove(self):
        if(self.stateTimer%16==0):
            self.av = random.random()*0.1 - 0.05
        if(self.stateTimer%64==0):
            if(random.random()<0.5):
                self.still=True
            else:
                self.still=False
        
        if(not self.still):
            self.angle +=self.av
            self.vel += np.array([np.cos(self.angle),np.sin(self.angle)]) * (self.health/(self.max_health/2)-1) * self.speed
    def attack(self):
        if self.stateTimer == 10:
            if self.target:
                self.target.hurt(0.5)
                self.heal(1)
            self.forcedMoodBehaviour()

class Vehicle(Entity):
    def __init__(self, pos,origin):
        super().__init__(pos,origin)
        self.health = 20
        self.topspeed = 5.0
        self.acc = 0.1

        self.roadtopspeed = 10.0
        self.roadacc = 0.2

        self.sideFriction = 0.95
        self.forwardFriction = 0.99
        self.braking = 0.9
        self.brakestop = 0.1
        self.handling = 0.1
        #self.traction = 0.1
        #self.turnTraction = 10.0
        #self.drift = 
        self.image = None

        self.fuel = 5000
        self.maxfuel = 5000

    def direction(self,shift=0):
        return np.array([np.cos(self.angle+shift),np.sin(self.angle+shift)])

    def update(self):


        # move
        

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
        
        self.pos+=self.vel

        if(world.tileCollision(self.pos,self.size)):
            self.pos-=self.vel
            self.vel = -0.1 * self.vel
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
        if self.fuel > 0:
            if(world.getTile(self.pos)==101):
                if(self.totalSpeed()<self.roadtopspeed):
                    self.vel+=self.roadacc*self.direction()
                    self.fuel -= 1
            else:
                if(self.totalSpeed()<self.topspeed):
                    self.vel+=self.acc*self.direction()
                    self.fuel -= 1

class RaceCar(Vehicle):
    idleImage = loadImage("vehicles/car.png")
    def __init__(self,pos,origin):
        super().__init__(pos,origin)
        self.image = RaceCar.idleImage

        self.topspeed = 4.5
        self.acc = 0.08
        self.roadtopspeed = 10.0
        self.roadacc = 0.2

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

        self.roadtopspeed = 5.0
        self.roadacc = 0.1

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

if __name__ == '__main__':

    world = World() 
    world.generateWorld()
    main()