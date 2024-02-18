import pygame
import random
import math
import noise
import numpy as np
import basinDrifter

world = basinDrifter.World() 
world.generateWorld()
factor = world.chunksize//2

screenWidth = world.worldsize*factor
screenHeight = world.worldsize*factor

gameDisplay = pygame.display.set_mode((screenWidth, screenHeight))
gameDisplay.fill((55,105,55))
groundImage=basinDrifter.loadImage("tiles/ground.png",size=factor)
sandImage=basinDrifter.loadImage("tiles/sand.png",size=factor)

#draw chunks and roads
for x in range(world.worldsize):
	for y in range(world.worldsize):
		c = world.chunks[y][x]

		if(c.chunktype%2==0):
			gameDisplay.blit(groundImage,(x*factor,y*factor,factor,factor))
			#pygame.draw.rect(gameDisplay,(0,x,y),(x*factor,y*factor,factor,factor))
		if(c.chunktype%2!=0):
			gameDisplay.blit(sandImage,(x*factor,y*factor,factor,factor))
			#pygame.draw.rect(gameDisplay,(255,255,255),(x*factor,y*factor,factor,factor))
		#if(len(c.roads)>1):
		#	pygame.draw.rect(gameDisplay,(0,255,255),(x*factor,y*factor,factor,factor))

		
		if(c.ends>0):
			pygame.draw.rect(gameDisplay,(255,0,0),(x*factor,y*factor,factor,factor))
		for [startpoint,endpoint] in c.roads:
			pygame.draw.line(gameDisplay,(0,0,0),factor*np.array([x,y])+startpoint//2,factor*np.array([x,y])+endpoint//2,2)


for x in range(world.worldsize):
	for y in range(world.worldsize):
		pass

#draw centerChunk
(x,y)=world.centerChunk.gridpos
pygame.draw.rect(gameDisplay,(255,0,0),(x*factor,y*factor,factor,factor))
#draw roads



running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # DRAW
    

    pygame.display.update() # flip?

pygame.quit()
quit()