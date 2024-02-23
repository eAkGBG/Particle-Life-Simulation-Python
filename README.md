#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 20:31:30 2024

@author: emil
"""
# Partikel Liv

Partikelsimulator baserad på youtube videos jag sett om Particle Life.
Den kör en partikel genererande klass i pygame som jag försökt optimera på 4 olika sätt.
Den numba optimerade versionerna väljs för närvarande i koden med OPTIMERA True/False
Med false lägger sig partiklarna snyggare intill varandra.
med den andra räknar vi genomsnitts positioner och vikter mot dom på alla partiklar och sparar i en dict av dicts för alla grid positioner. som vi kan söka igenom.
så vi har en cashe att söka igenom för att göra beräkningar på våran förflyttnings vektor.
Det finns mycket till att implimentera i denna koden.
för att få klickbara inställningar ocksåvidare.
Num partiklar 20 ger rätt bra prestanda och intressanta animationer. det skapar 20*4 partiklar.
typer av partiklar koden klarar av att generera hur många typer och slumpade vikter man vill. bara titta nere vid initieringen av partikelsystemet ovan pygame loopen.

Pil upp skapar nya slumpade vikter om man inte orkar vänta dom förinställda 60sekunderna på en ny generation av slumpade vikter.
RECORD True/False skärminspelning av pygame fönstret. tar en screenshot i ram och genererar en video utifrån detta.

Att göra:
    släng in meny
    låt användaren spara vikter i json fil för intressanta simuleringar.
    delta T inte riktigt implimenterad den är beroend nu av FPS.
    ska vara en dämpningsfaktor oberoende av FPS inställningen.
    implimentera klumpar med egna vikter då den riktiga particle life ska låta dig skapa intressanta organismer och slänga in klumparm ed sådana. att rendera.
    en annan version jag sett skapar utomatiskt klumpar under körningens gång. det hade varit intressant kanske att köra exempelvis klumpar med slumpade vikter.
    som man sedan kan spara under körningen för att experimentera fram intressanta organismer.

## Installation

För att installera de nödvändiga paketen, kör följande kommandon:

```bash
# Med pip:
pip install pygame
pip install numpy
pip install opencv-python
pip install numba

# Med conda:
conda install -c cogsci pygame
conda install numpy
conda install -c conda-forge opencv
conda install numba# Particle-Life-Simulation-Python
