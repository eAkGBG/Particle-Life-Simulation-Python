#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 11:55:37 2024

@author: emil
"""

import pygame
import numpy as np
import random
#import math
import cv2
from pprint import pprint
from numba import jit, float64
from numpy.linalg import norm
from concurrent.futures import ThreadPoolExecutor

@jit(float64(float64[:]), nopython=True)
def my_norm(x):
    return np.sqrt(np.sum(x**2))


# Konstanter
# Optimering inte längre en prestanda optimering utan man kanske kan se den som en pressisions optimering ? 
#OPTIMERA = False
OPTIMERA = True
#NUMBA_OPT = False
NUMBA_OPT = True

#RECORD = True
RECORD = False

VIDEO_FIL = 'particle_life_sim.mp4'
#SCREENSHOT = 'frame_to_render.png'


#PARALLEL = True
#PARALLEL = False

# Fysik
PARTIKELSTORLEK = 12
MASS = 1 ## Här kan man ställa in partiklarnas massa om man känner för detta. 1är standardvärdet.
MAX_PART_BERAKNING = 10 #10 ger ett fint resultat. Här kan man ändra om man har en super dator hur många beräkningar på partiklar runtom vi låter varje partikel göra. Under 10 är att rekomendera över 50*4typer

ATTRAKTION_MAX = -20 ## här väljer vi vikter för att skapa slumpade attraktions vikter för varje partikel typ.  -20 man kan testa med kanske -10 till -20
REPULSION_MAX = 20 ## här väljer vi vikter för att skapa slumpade attraktions vikter för varje partikel typ.    20 funkar rätt okej. man kan testa med kanske 10 till 20
DAMPNINGSKRAFT_TID = 0.7 ## varje frame minskar vi hastighets vektorn med detta. 0.55 är okej. 0.5 är standardvärdet.
KOLLISIONS_KRAFT = 0.35 ## Denna kraften påverkar hur kraftigt vi stöter bort partiklar som nuddar varandra.

# Fönster
FPS = 25
WIDTH = 1920
HEIGHT = 1080
#WIDTH = 1000
#HEIGHT = 1000
if OPTIMERA == True:
    GRID_SCALE = PARTIKELSTORLEK
    # Sök avstånd
    SOK_AVSTAND = 8
else:
    GRID_SCALE = 20
    # Sök avstånd
    SOK_AVSTAND = 4




NUM_PARTIKLAR = 30 ## Runt 50*4 typer ger bra prestanda och intressanta interaktioner.


# färger för vår breed Valde några pasteller för att representera Röd Grön Blå Gul 
## Vi använde detta i våran gamla kod fina färger kanske kommer till nytta senare.
PART_BREED_COLOR = [(240, 125, 160),
                    (102, 245, 103),
                    (102, 125, 249),
                    (252, 253, 152)
                    ]

@jit(float64[:, :](float64, float64, float64, float64[:], float64[:], float64[:]), nopython=True)
def numba_kraft_berakning(M, K, G, egen_pos, egen_velocity, kompis_pos):
    M = M
    K = K
    G = G
        
    # Kör våran G krafts beräkning.
    R_vektor = kompis_pos - egen_pos
    if np.all(R_vektor == 0):  # Kontroll för grid beräkning så vi inte räknar om vi har medel värdet från en cell som endast består av self
        return np.empty((0, len(egen_velocity)))  # Returnera en tom 2D-array istället för None
    
    #R = my_norm(R_vektor)
    R = norm(R_vektor)
    
    if OPTIMERA == True: # Då vi kör funktionen som ger os en multiplicerad kraft på alla partiklar runtom som vi stoppar in i M så får vi hantera detta.
        F = (G/M) / R**2 # Det gör vi här vänder tillbaka kraften så den blir mot 1 partikel istället.
        #egen_velocity += F * R_vektor Vi byter ordning på beräkningarna så att vi kan använda kraften baserad på massan då vi plockat in kraften tidigare skalad.
    
        if R < PARTIKELSTORLEK + PARTIKELSTORLEK: # Om partiklarna krockar så är vi under deras radier tilsammans.
            overlappning = PARTIKELSTORLEK + PARTIKELSTORLEK - R # här räknar vi ut hur mycket vi överlappar varandra.
            
            F_kollision = K * overlappning # Kolissions dämpande kraft.
           
            egen_velocity  -= F_kollision * R_vektor / (R + 0.0000001) # förhindrar division med 0.
        if R > 1:    
            F = G / R**2
            egen_velocity += F * R_vektor
        else:
            return np.empty((0, len(egen_velocity)))  # Returnera en tom 2D-array istället för None
        
        result = np.empty((3, len(egen_velocity)))  # Skapa en 2D-array för att lagra resultaten
        result[0, :] = egen_velocity
        result[1, :] = R_vektor
        result[2, 0] = R  # Lägg till R som det första elementet i den tredje raden
        return result
    else:
        if R > 1:  
            F = G / R**2
            egen_velocity += F * R_vektor
            
        if R < PARTIKELSTORLEK + PARTIKELSTORLEK: # Om partiklarna krockar så är vi under deras radier tilsammans.
            overlappning = PARTIKELSTORLEK + PARTIKELSTORLEK - R # här räknar vi ut hur mycket vi överlappar varandra.
            
            F_kollision = K * overlappning # Kolissions dämpande kraft.
            
            egen_velocity  -= F_kollision * R_vektor / (R + 0.0000001) # förhindrar division med 0.
        else:
            return np.empty((0, len(egen_velocity)))  # Returnera en tom 2D-array istället för None
        
        result = np.empty((3, len(egen_velocity)))  # Skapa en 2D-array för att lagra resultaten
        result[0, :] = egen_velocity
        result[1, :] = R_vektor
        result[2, 0] = R  # Lägg till R som det första elementet i den tredje raden
        return result
            

    
    
class PartikelCluster():
    partiklar = []
    partiklar_markta_att_radera = []
    partikel_typer = {}
    partikel_typer_attraktioner = {}
    grid = None
    grid_cell_cashe = {}
    
    grid_scale = 100
    width = 200
    height = 200
    partikel_storlek = PARTIKELSTORLEK
    
    def __init__(self):
        # Skapa en lista med färger för våra partikeltyper
        pass
    
    @classmethod
    def update_grid_cell_cashe(cls):
        if OPTIMERA == False:
            pass
        else: 
        # Förberäkna medelpositioner och antal partiklar för varje cell och partikeltyp
            PartikelCluster.grid_cell_cashe = {}
            for i in range(PartikelCluster.grid.shape[0]):
                for j in range(PartikelCluster.grid.shape[1]):
                    cell = PartikelCluster.grid[i][j]
                    if cell is not None and len(cell) > 0:
                        PartikelCluster.grid_cell_cashe[(i, j)] = {}
                        for partikel in cell: #skapa dict för varje typ och antalet partiklar där i [0][1]
                            if partikel.partikel_typ not in PartikelCluster.grid_cell_cashe[(i, j)]:
                                PartikelCluster.grid_cell_cashe[(i, j)][partikel.partikel_typ] = [[partikel.position], 1]
                            else:
                                PartikelCluster.grid_cell_cashe[(i, j)][partikel.partikel_typ][0].append(partikel.position)
                                PartikelCluster.grid_cell_cashe[(i, j)][partikel.partikel_typ][1] += 1
            
            # Beräkna medelpositioner
            for cell in PartikelCluster.grid_cell_cashe:
                for partikel_typ in PartikelCluster.grid_cell_cashe[cell]:
                    PartikelCluster.grid_cell_cashe[cell][partikel_typ][0] = np.mean(PartikelCluster.grid_cell_cashe[cell][partikel_typ][0], axis=0)


    @classmethod
    def set_grid(cls, x=None, y=None, grid_scale=None):
        # En set funktion att kalla för att bygga våran np grid att hålla reda på partiklar. detta gör att vi bör kunna omskala den.
        # Först kollar vi av våra variablerf och använder våra standard värden om vi inte anget några egna.
        x = x if x is not None else cls.width
        y = y if y is not None else cls.height
        grid_scale = grid_scale if grid_scale is not None else cls.grid_scale
        # Om vi angett egna uppdaterar vi våra klass variabler så partiklar kan dra nytta av dem.
        cls.width = x
        cls.height = y
        cls.grid_scale = grid_scale
        
        # Här skapar vi våran grid 1 större för att skydda oss från partiklar som överträder index.
        cls.grid = np.empty((x // grid_scale + 1, y // grid_scale + 1), dtype=object)
        for i in range(cls.grid.shape[0]):
            for j in range(cls.grid.shape[1]):
                cls.grid[i,j] = []
                
        print('Grid shape vid initieringen.:',PartikelCluster.grid.shape)
    @classmethod            
    def add_partikel(cls, x, y, typ=0):
        # Skapa en ny färg om typen inte redan finns. Denna kanske vi kan lägga till så vi inte skapar färger för lika andra färger.
        if typ not in PartikelCluster.partikel_typer.keys():
            PartikelCluster.partikel_typer[typ] = []
            # Ljusa färger.
            r = random.randint(100, 250)
            g = random.randint(100, 250)
            b = random.randint(100, 250)
            a = 255
            color = (r, g, b, a)
            PartikelCluster.partikel_typer[typ] = color
            
        # print('Partikel Typer Attraktions Dict: ',PartikelCluster.partikel_typer_attraktioner, '\n')
        if typ not in PartikelCluster.partikel_typer_attraktioner.keys():
            # Skapa en dict för den nya typen
            PartikelCluster.partikel_typer_attraktioner[typ] = {}
            for existerande_typ in PartikelCluster.partikel_typer_attraktioner.keys():
                # Generera ett random värde för varje par av partikeltyper
                random_value = random.uniform(ATTRAKTION_MAX, REPULSION_MAX)
                # Lägg till alla Befintliga typer till den nya dicten med random värde
                PartikelCluster.partikel_typer_attraktioner[typ][existerande_typ] = random_value
                # Uppdatera alla existerand dicts med våran nya typ.
                if existerande_typ != typ:  # undvik att uppdatera den nya typen igen
                    PartikelCluster.partikel_typer_attraktioner[existerande_typ][typ] = random.uniform(ATTRAKTION_MAX, REPULSION_MAX)
        
        partikel = cls.Partikel()
        partikel.partikel_typ = typ
        partikel.color = PartikelCluster.partikel_typer[typ]
        partikel.position = np.array([x,y], dtype=float)
        partikel.set_grid_pos()
        partikel.set_partikel_sprite()
        partikel.set_partikel_attraktion_lista(typ)
        cls.partiklar.append(partikel)
    
    @classmethod
    def del_markta_partiklar(cls):
        for partikel in cls.partiklar_markta_att_radera:
            cls.partiklar.remove(partikel)
        cls.partiklar_markta_att_radera.clear()


    @classmethod
    def update(cls, screen):
        cls.update_grid_cell_cashe()
        for partikel in cls.partiklar:
            partikel.update()
            cls.render_partikel(screen, partikel)
        for partikel in cls.partiklar:
            partikel.set_grid_pos()

    @classmethod 
    def set_nya_random_attraktioner(cls):
        PartikelCluster.partikel_typer_attraktioner = None
        PartikelCluster.partikel_typer_attraktioner = {}
        for partikel in PartikelCluster.partiklar:
            typ = partikel.partikel_typ
            if typ not in PartikelCluster.partikel_typer_attraktioner.keys():
                # Skapa en dict för den nya typen
                PartikelCluster.partikel_typer_attraktioner[typ] = {}
                for existerande_typ in PartikelCluster.partikel_typer_attraktioner.keys():
                    # Generera ett random värde för varje par av partikeltyper
                    random_value = random.uniform(ATTRAKTION_MAX, REPULSION_MAX)
                    # Lägg till alla Befintliga typer till den nya dicten med random värde
                    PartikelCluster.partikel_typer_attraktioner[typ][existerande_typ] = random_value
                    # Uppdatera alla existerand dicts med våran nya typ.
                    if existerande_typ != typ:  # undvik att uppdatera den nya typen igen
                        PartikelCluster.partikel_typer_attraktioner[existerande_typ][typ] = random.uniform(ATTRAKTION_MAX, REPULSION_MAX)
        for partikel in PartikelCluster.partiklar:
            partikel.set_partikel_attraktion_lista(partikel.partikel_typ)
    
    # För att kunna ställa en custom attraktion för en partikel typ. behöver vi skicka in en lista med vilka typer som finns i systemet.
    # Så att vi vet hur många vikter vi behöver skapa i en custom attraktion att stoppa in i våran dict över partikeltyper och vikter så vi kan använda dem i våran globala attraktions beräkning.
    # Efter vi skickat in en lista med partikeltyper så behöver vi skicka in en lista med attraktions vikter för varje partikel typ.
    # Sedan behöver vi göra något snarlikt våran skapa random vikter. gå igenom alla partikeltyper och skapa en dict med nyckel värden som är partikel typen och värden som är attraktions vikten.        
    @classmethod
    def set_custom_attraktion(cls, typ, attraktion_list):
        PartikelCluster.partikel_typer_attraktioner[typ] = {}
        PartikelCluster.partikel_typer_attraktioner[typ] = attraktion_list
        #for i, partikel_typ in enumerate(PartikelCluster.partikel_typer_attraktioner.keys()):
        #    PartikelCluster.partikel_typer_attraktioner[typ][partikel_typ] = attraktion_list[i]
        #    if partikel_typ != typ:
        #        PartikelCluster.partikel_typer_attraktioner[partikel_typ][typ] = attraktion_list[i]
        for partikel in PartikelCluster.partiklar:
            partikel.set_partikel_attraktion_lista(partikel.partikel_typ)
    
    # För att kunna ställa en custom attraktion för en partikel typ. behöver vi läsa in en dict med attraktioner för varje partikel typ.
    # Dicten ska ha nyckel värden som är partikel typen och värden som är attraktions vikten.
    # För att kunna hålla reda på alla partikeltyper som finns i systemet behöver vi plocka ut vilka typer som finns i systemet.
    # Så att vi vet hur många vikter vi behöver skapa i en custom attraktion att stoppa in i våran dict över partikeltyper och vikter så vi kan använda dem i våran globala attraktions beräkning.        
    @classmethod
    def get_partikel_typer(cls):
        return list(PartikelCluster.partikel_typer.keys())
    
    # vi behöver funktionaliteten att hämta ut vikterna från en typ.
    @classmethod
    def get_partikel_typ_attraktioner(cls, typ):
        return PartikelCluster.partikel_typer_attraktioner[typ]
    
    @classmethod
    def get_partikel_typ_farger(cls):
        return PartikelCluster.partikel_typer
    
    def render_partikel(screen, partikel=None):
        if partikel is not None:
            screen.blit(partikel.partikel_sprite, (int(partikel.position[0]),int(partikel.position[1])))
        else:
            print('Det blev fel vi fick inget partikel objekt att rita!')
    
    class Partikel():
        def __init__(self):
            self.position = np.zeros((2), dtype=float)
            self.velocity = np.zeros((2), dtype=float)
            self.grid_pos = None
            self.partiklar_nara = None
            self.partikel_typ = None
            self.partikel_attraktion_lista = None
            self.radie = PartikelCluster.partikel_storlek
            self.color = None
            self.color_dark = None
            self.partikel_sprite = None
        
        def set_partikel_attraktion_lista(self, typ):
            self.partikel_attraktion_lista = PartikelCluster.partikel_typer_attraktioner[typ]
            
        def set_partiklar_nara(self):
            if OPTIMERA == True:
                pass
            else:
                if self.grid_pos is not None:
                    x,y = self.grid_pos
                    self.partiklar_nara = None
                    #print('x och y efter = self.grid_pos x:', x, ' y:', y)
                    # kontrollera index passar våran grid.
                    min_y = max(0, y - SOK_AVSTAND)
                    max_y = min(PartikelCluster.grid.shape[1], y + (SOK_AVSTAND +1))
                    min_x = max(0, x- SOK_AVSTAND)
                    max_x = min(PartikelCluster.grid.shape[0], x + (SOK_AVSTAND + 1))
                        
                    # skapa en lista med partiklar nxn grid runtom oss.
                    # Se till att self.partiklar_nara är tom
                    #self.partiklar_nara = None
                    self.partiklar_nara = {}

                    # En loop som går igenom alla grid positioner +- n utifrån våran boid. ve behöver gå 1över för att få ett pga att range stoppar 1 steg innan siffran (räkna från 0)
                    for x in range(min_x, max_x):
                        for y in range(min_y, max_y):
                            if PartikelCluster.grid[x,y] is not None:
                                for partikel in PartikelCluster.grid[x, y]:
                                    # Lägg in våran partikel i dict med nyckel namn på breed.
                                    if partikel.partikel_typ not in self.partiklar_nara:
                                        self.partiklar_nara[partikel.partikel_typ] = []
                                    self.partiklar_nara[partikel.partikel_typ].append(partikel)
                                    
                                    # Sortera partiklarna i varje breed baserat på avståndet till den aktuella partikeln
                    for partikel_typ in self.partiklar_nara.keys():
                        self.partiklar_nara[partikel_typ] = sorted(self.partiklar_nara[partikel_typ], key=lambda partikel: np.linalg.norm(self.position - partikel.position))
    
                    # om vi inte hittar några andra partiklar. sätt dict till None.
                    if list(self.partiklar_nara.keys()) == [self.partikel_typ] and self.partiklar_nara[self.partikel_typ] == [self]:
                        self.partiklar_nara = None

            
            
        def set_grid_pos(self):
            # Kontrollera om vi finns i grid eller inte. om vi gör det tar vi bort oss själva för att stoppa in oss i våran nya grid.
            if self.grid_pos is not None:
                PartikelCluster.grid[self.grid_pos[0], self.grid_pos[1]].remove(self)
            ny_grid_pos = (int(self.position[0] // PartikelCluster.grid_scale), int(self.position[1] // PartikelCluster.grid_scale))
            #ny_grid_pos = (int(self.position[0] // GRID_SCALE), int(self.position[1] // GRID_SCALE))
            
            self.grid_pos = ny_grid_pos
            #print('Self.grid_pos: ',self.grid_pos)
            #PartikelCluster.grid[tuple(ny_grid_pos)].append(self) #här gör vi en tupe omvandling numpy kräver tydligen att index är en tuple inte en array.
            PartikelCluster.grid[ny_grid_pos[0], ny_grid_pos[1]].append(self)
            
        def set_partikel_sprite(self):
            # Skapa våran mörka färg. med alpha värde 50 av 255
            self.color_dark = (max(self.color[0] - 50, 0), max(self.color[1] - 50, 0), max(self.color[2] - 50, 0), 50)
            # Skapa en surface till våran sprite.
            partikel_yta = pygame.Surface((PartikelCluster.partikel_storlek * 2,PartikelCluster.partikel_storlek * 2), pygame.SRCALPHA)
            partikel_yta.fill((0, 0, 0, 0))
            
            # Rita våran mörka cirkel
            pygame.draw.circle(partikel_yta, (self.color_dark), (PartikelCluster.partikel_storlek, PartikelCluster.partikel_storlek), PartikelCluster.partikel_storlek)
            
            # Rita våran prick
            pygame.draw.circle(partikel_yta, (self.color), (PartikelCluster.partikel_storlek, PartikelCluster.partikel_storlek), PartikelCluster.partikel_storlek - 3)
            
            self.partikel_sprite = partikel_yta.copy()
            
        def update(self):

            self.set_partiklar_nara()
            if NUMBA_OPT == True:
                self.numba_global_attraktion_kraft()
                self.numba_global_attraktion_kraft_grid()
            else:
                self.global_attraktion_kraft()
                self.global_attraktion_kraft_grid()

            
            
            self.velocity *= DAMPNINGSKRAFT_TID # Här ska vi använda Delta T om jag förstått videor på iunternet rätt. men jag kör bara en enkel dämpningsfaktor.
            self.position += self.velocity
            
            # Klippa positionen till att vara inom fönstret
            self.position[0] = np.clip(self.position[0], 0, PartikelCluster.width)
            self.position[1] = np.clip(self.position[1], 0, PartikelCluster.height)
            # Teleportera till andra sidan om vi kommer för nära kanten.
            # för X
            if self.position[0] <= 0:
                self.position[0] = WIDTH
            elif self.position[0] >= WIDTH:
                self.position[0] = 0
            # För Y
            if self.position[1] <= 0:
                self.position[1] = HEIGHT
            elif self.position[1] >= HEIGHT:
                self.position[1] = 0

        def global_attraktion_kraft(self):
            if OPTIMERA == True:
                pass
            else:
                #G = 1 # påhittad Gkraft
                M = MASS # alla partiklar får samma massa.
                K = KOLLISIONS_KRAFT # kollisions motverkande kraft. 0.2 är okej vi testar lägre.
                #for partikel in PartikelCluster.partiklar:
                max_berakningar = MAX_PART_BERAKNING
                
                if self.partiklar_nara is not None:
                    for partikel_typ in self.partiklar_nara.keys():
                        berakningar = 0
                        for partikel in self.partiklar_nara[partikel_typ]:
                            G = self.partikel_attraktion_lista[partikel_typ]
                            #berakningar = 0
                            if partikel is not self:
                                R_vektor = partikel.position - self.position
                                R = np.linalg.norm(R_vektor)
                                if R > 1: #för våran fina kraft.
                                #if R > 0: # såhär gör andra.
                                    #F = G * (M*M) / R**2 # här räknar vi gravitations kraften. men jag tror vi kan ändra på den. till någon roligare kraft.
                                    #F = G * M / R # här räknar vi gravitations kraften. men jag tror vi kan ändra på den. till någon roligare kraft.
                                    # F = G * M / R**2 #Riktiga gravitationen tog bort ett M då vi ändå har massa 1
                                    # F_vektor = F * (R_vektor / R)
                                    # self.velocity += F_vektor
                                    
                                    ##Denna kraften ger ett långsamt vackert resultat.
                                    F = G / R**2
                                    self.velocity += F * R_vektor
                                if R < self.radie + partikel.radie: # Om partiklarna krockar så är vi under deras radier tilsammans.
                                    overlappning = self.radie + partikel.radie - R # här räknar vi ut hur mycket vi överlappar varandra.
                                    F_kollision = K * overlappning # Kolissions dämpande kraft.
                                    self.velocity -= F_kollision * R_vektor / (R + 0.0000001) # förhindrar division med 0.
                                berakningar += 1
                                if berakningar >= max_berakningar:
                                    break
                                
        def numba_global_attraktion_kraft(self):
            if OPTIMERA == True:
                pass
            else:
                #G = 1 # påhittad Gkraft
                M = MASS # alla partiklar får samma massa.
                K = KOLLISIONS_KRAFT # kollisions motverkande kraft. 0.2 är okej vi testar lägre.
                #for partikel in PartikelCluster.partiklar:
                max_berakningar = MAX_PART_BERAKNING
                
                if self.partiklar_nara is not None:
                    for partikel_typ in self.partiklar_nara.keys():
                        berakningar = 0
                        for partikel in self.partiklar_nara[partikel_typ]:
                            G = self.partikel_attraktion_lista[partikel_typ]
                            if partikel is not self:
                                temp = numba_kraft_berakning(np.float64(M), np.float64(K), np.float64(G), self.position, self.velocity, partikel.position)

                                if len(temp) > 0:
                                   self.velocity = temp[0]
                                   #R_vektor = temp[1]
                                   #R = temp[2, 0]
                                       
                                berakningar += 1
                                if berakningar >= max_berakningar:
                                    break
                            

        def global_attraktion_kraft_grid(self):
            if OPTIMERA == False:
                pass
            else:
                M = MASS # alla partiklar får samma massa.
                K = KOLLISIONS_KRAFT # kollisions motverkande kraft. 0.2 är okej vi testar lägre.
                # denna funktionen ska försöka vara super optimerad global attraktions beräkning
                x,y = self.grid_pos # fånga grid position
    
                # kontrollera index passar våran grid.
                min_y = max(0, y - SOK_AVSTAND)
                max_y = min(PartikelCluster.grid.shape[1], y + (SOK_AVSTAND + 1))
                min_x = max(0, x - SOK_AVSTAND)
                max_x = min(PartikelCluster.grid.shape[0], x + (SOK_AVSTAND + 1))
                
                #total_vektor = np.zeros(2) # här i ska vi spara våran totala vektor beräknad från summan alla grid runtom.
                partikel_typ_i_cell = {}
                
                for i in range(min_x, max_x):
                    for j in range (min_y, max_y):
                        if (i, j) in PartikelCluster.grid_cell_cashe:
                            for partikel_typ in PartikelCluster.grid_cell_cashe[(i, j)]:
                                partikel_typ_i_cell_avg_possition, antal_partiklar = PartikelCluster.grid_cell_cashe[(i, j)][partikel_typ]

                                #partikel_typ_i_cell_avg_possition = np.mean([partikel.position for partikel in partikel_typ_i_cell[nyckel]],  axis=0)
                                G = self.partikel_attraktion_lista[partikel_typ] * antal_partiklar
                                R_vektor = partikel_typ_i_cell_avg_possition - self.position
                                if np.all(R_vektor != 0):
                                    R = np.linalg.norm(R_vektor)
                                    #if R > 1: #för våran fina kraft.
                                    if R > 1: # såhär gör andra.
                                        # #F = G * (M*M) / R**2 # här räknar vi gravitations kraften. men jag tror vi kan ändra på den. till någon roligare kraft.
                                        # #F = G * M / R # här räknar vi gravitations kraften. men jag tror vi kan ändra på den. till någon roligare kraft.
                                        # F = G * M / R**1.25 #Här är en lite roligare mitimellan kraft ?
                                        # #F = G * M / R**2 #Riktiga gravitationen tog bort ett M då vi ändå har massa 1
                                        # F_vektor = F * (R_vektor / (R + 0.0000001))
                                        # self.velocity += F_vektor
                                        
                                        ##Denna kraften ger ett långsamt vackert resultat.
                                        F = G / R**2
                                        self.velocity += F * R_vektor
                                    if R < self.radie * 2: # Om partiklarna krockar så är vi under deras radier tilsammans.
                                        F = (G/antal_partiklar) / R**2
                                        overlappning = (self.radie * 2) - R # här räknar vi ut hur mycket vi överlappar varandra.
                                        F_kollision = K * overlappning # Kolissions dämpande kraft.
                                        self.velocity -= F_kollision * R_vektor / (R + 0.0000001) # förhindrar division med 0.
                                else:
                                    continue
                            

        def numba_global_attraktion_kraft_grid(self):
            if OPTIMERA == False:
                pass
            else:
                M = MASS # alla partiklar får samma massa.
                K = KOLLISIONS_KRAFT # kollisions motverkande kraft. 0.2 är okej vi testar lägre.
                # denna funktionen ska försöka vara super optimerad global attraktions beräkning
                x,y = self.grid_pos # fånga grid position
    
                # kontrollera index passar våran grid.
                min_y = max(0, y - SOK_AVSTAND)
                max_y = min(PartikelCluster.grid.shape[1], y + (SOK_AVSTAND + 1))
                min_x = max(0, x - SOK_AVSTAND)
                max_x = min(PartikelCluster.grid.shape[0], x + (SOK_AVSTAND + 1))
                
                
                for i in range(min_x, max_x):
                    for j in range (min_y, max_y):
                        if (i, j) in PartikelCluster.grid_cell_cashe:
                            for partikel_typ in PartikelCluster.grid_cell_cashe[(i, j)]:
                                partikel_typ_i_cell_avg_possition, antal_partiklar = PartikelCluster.grid_cell_cashe[(i, j)][partikel_typ]

                                G = self.partikel_attraktion_lista[partikel_typ] * antal_partiklar
                                M = antal_partiklar #då vi inte orkar skriva om numba_kraft_berakning. så kan vi hysta in M där. det blir en bra representation av Massa :)
                                temp = numba_kraft_berakning(np.float64(M), np.float64(K), np.float64(G), self.position, self.velocity, partikel_typ_i_cell_avg_possition)
                                if len(temp) > 0:
                                    self.velocity = temp[0]
                                    #R_vektor = temp[1]
                                    #R = temp[2, 0]

                                        
                                else:
                                    continue
                             

                    
# Create a VideoWriter object
if RECORD == True:    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    video = cv2.VideoWriter(VIDEO_FIL, fourcc, FPS, (WIDTH, HEIGHT))

# Skapa partikelsystemet och initiera
partikelsystemet = PartikelCluster()
partikelsystemet.set_grid(WIDTH, HEIGHT, GRID_SCALE)

pygame.init()
import meny_klass



screen = pygame.display.set_mode((WIDTH, HEIGHT))
font_fps_raknare = pygame.font.Font(None, 42)
font_vikter = pygame.font.Font(None, 18)
timer_fps_uppdatering = 0 # variabel till våran timer för att random uppdatera vikter och annat skoj.
sekunder = 1 # initiera våran timer.
senaste_uppdatering = 0 # initiera våran kontroll om vi kört random uppdatering eller ej redan för given minut.

#Skapa ett gäng partiklar.
for _ in range(NUM_PARTIKLAR):
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 0)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 1)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 2)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 3)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 4)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 5)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 6)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 7)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 8)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 9)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 10)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 11)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 12)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 13)
    partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), 14)
# Main pygame Loop
running = True
clock = pygame.time.Clock()

meny = meny_klass.set_partikel_vikter(partikelsystemet, 10, 30, 400, 300)

while running:
    # skapa Delta Tid och håll våran fps.
    dt = clock.tick(FPS) / 1000.0
    #clock.tick(FPS)
    
    screen.fill((21, 20, 57))
    sekunder = sekunder + 1 if timer_fps_uppdatering % FPS == 0 else sekunder
    minuter = sekunder // 60
    
    if minuter > senaste_uppdatering:
        partikelsystemet.set_nya_random_attraktioner()
        senaste_uppdatering = minuter
    

    partikelsystemet.update(screen)

    
    # # Skriv ut vikterna
    # y_offset = 50
    # for typ, inner_dict in PartikelCluster.partikel_typer_attraktioner.items():
    #     color = PartikelCluster.partikel_typer[typ]
    #     for inner_typ, vikt in inner_dict.items():
    #         vikt_text = font_vikter.render(f'Vikt mellan {typ} och {inner_typ}: {vikt:.2f}', 1, (color))
    #         screen.blit(vikt_text, (10, y_offset))
    #         y_offset += 30  # Flytta ner nästa rad text    
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        #### Kod för att bara ändra varje gång man tryckt en gång på tangenten.
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                partikelsystemet.set_nya_random_attraktioner()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Musklick upptäckt, kontrollera om någon knapp klickades på
            for button in meny.knappar:
                if button.is_over(pygame.mouse.get_pos()):
                    meny.clicked()
                #partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10), random.randint(0, 3))
        
    # #### Kod för att hålla inne tangenter.
    # keys = pygame.key.get_pressed()
    # if keys[pygame.K_UP]: 
    #     partikelsystemet.add_partikel(random.uniform(10, WIDTH -10), random.uniform(10, HEIGHT -10))
        

    

    #tid_tagar_ur = font_fps_raknare.render(f'FPS:{round(clock.get_fps(), 1)} Timer: {str(sekunder // 60)}:{str(sekunder % 60)} (60sek new random attraction weights!)', True, (255, 255, 255))
    tid_tagar_ur = font_fps_raknare.render(f'Timer: {str(sekunder // 60)}:{str(sekunder % 60)} (Every 60sek, new random lifeforms!)', True, (255, 255, 255))
    tid_tagar_ur_forskjutning_pixlar = tid_tagar_ur.get_rect().width
    tid_tagar_ur_bakgrund = pygame.Surface(tid_tagar_ur.get_size())
    tid_tagar_ur_bakgrund.fill((11, 10, 47))
    tid_tagar_ur_bakgrund.set_alpha(100)
    screen.blit(tid_tagar_ur_bakgrund,((WIDTH // 2) - (tid_tagar_ur_forskjutning_pixlar // 2) ,10))
    screen.blit(tid_tagar_ur,((WIDTH // 2) - (tid_tagar_ur_forskjutning_pixlar // 2) ,10))
    
#    # skapa en text yta att rendera fps mätaren.
#    text = font_fps_raknare.render('FPS: {0:.2f} Timer: {1:.0f}:{2:.0f}'.format(clock.get_fps(), sekunder // 60, sekunder % 60), 1, (255,255,255))
#    # måla ut texten.
#    screen.blit(text, (WIDTH // 2, 20))
    
    meny.draw(screen)
    #knapp.draw(screen)
    pygame.display.flip()
    #pygame.display.update()
    # Spela in video från simuleringen.
    if RECORD == True:
        # Konvertera Pygame Surface till en numpy array
        frame = pygame.surfarray.array3d(screen)
        # Transponera arrayen för att matcha det format som cv2 förväntar sig cv2 vill ha en frame (höjd, bredd, 3). pygame ger en (bredd, Höjd, 3) så vi vänder på dom.
        frame = np.transpose(frame, (1, 0, 2))
        # Konvertera färgrymden från RGB till BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        #skriv frame til lvideo.
        video.write(frame)
    

    timer_fps_uppdatering += 1
# Avsluta spelet.
if RECORD == True:
    video.release()
pygame.quit()