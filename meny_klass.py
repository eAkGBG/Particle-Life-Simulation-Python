import pygame

class Button:
    def __init__(self, color, x, y, width, height, text='', text_color=(255,255,255)):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.text_color = text_color  # Ny parameter för textfärgen

    def draw(self, screen, outline=None):
        knapp_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        knapp_surface.fill(self.color)
        screen.blit(knapp_surface, (self.x, self.y))

        if self.text != '':
            font = pygame.font.SysFont(None, 36)
            text = font.render(self.text, 1, self.text_color)  # Använd textfärgen här
            text_x = max(self.x, self.x + (self.width/2 - text.get_width()/2))
            text_y = self.y + (self.height/2 - text.get_height()/2)
            screen.blit(text, (text_x, text_y))
    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False
    
    def click(self):
        print(self.text)
        return self.text

    
# En klass att bygga en meny där man kan välja en partikeltyp. och ställa in dess attraktion och repulsion vikter.
# den behöver hämta ut vilka typer som finns från partikel systemet.
# partikelsystem.get_partikel_typer()
# den ska kunna skapa partikelvikter med knappar +- 1 och 10
# den ska använda partikelsystem.set_custom_attraktion(typ, attraktion_list) där lista är en lista med attraktioner för varje partikeltyp
class set_partikel_vikter:
    def __init__(self, partikelsystem, x, y, width, height):
        self.partikelsystem = partikelsystem
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.knappar = []
        self.typ = 0
        self.vikter = []
        self.typ_text = None
        self.attraktion = 0
        self.repulsion = 0
        self.status = 'main'  # Lägg till en statusvariabel
        self.skapa_main_knappar()  # Skapa huvudmenyn när objektet skapas
        self.selected_weight = 0
        self.partikel_farger = {}
     
    def set_partikel_farger(self):
        self.partikel_farger = self.partikelsystem.get_partikel_typ_farger()
            
    def set_lista_partikel_typer(self):
        self.lista_partikel_typer = self.partikelsystem.get_partikel_typer()
        
    # Skapar knappar för att välja partikeltyp
    def skapa_main_knappar(self):
        self.status = 'main'
        self.set_lista_partikel_typer()
        self.set_partikel_farger()
        self.knappar = []
        for i in range(len(self.lista_partikel_typer)):
            typ = self.lista_partikel_typer[i]
            farg = self.partikel_farger[typ]  # Hämta färgen för denna partikeltyp
            self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + i*30, 100, 25, str(typ), text_color=farg))  # Skicka färgen till Button
    
    # om vi klickat en knapp vill vi ställa in vikterna för den partikeln
    # så vi ställer typen till den vi klickat på
    # och skapar knappar för att ställa in vikterna
    # vi kan hämpta nuvarande vikter med self.partikelsystem.get_partikel_typ_attraktioner(typ)        
    def clicked(self):
        for knapp in self.knappar:
            if knapp.is_over(pygame.mouse.get_pos()):
                if self.status == 'main':
                    self.typ = int(knapp.click())
                    self.typ_text = str(self.typ)
                    self.vikter = self.partikelsystem.get_partikel_typ_attraktioner(self.typ)
                    self.status = 'select_weight'
                    self.skapa_select_weight_knappar()
                elif self.status == 'select_weight':
                    self.selected_weight = int(knapp.click())
                    self.status = 'weights'
                    self.skapa_vikter_knappar()
                elif self.status == 'weights':
                    if knapp.text == '+1':
                        self.vikter[self.selected_weight] += 1
                    elif knapp.text == '+10':
                        self.vikter[self.selected_weight] += 10
                    elif knapp.text == '-1':
                        self.vikter[self.selected_weight] -= 1
                    elif knapp.text == '-10':
                        self.vikter[self.selected_weight] -= 10
                    self.partikelsystem.set_custom_attraktion(self.typ, self.vikter)
                    self.status = 'main'
                    self.skapa_main_knappar()
                
    # skapar knappar för att ställa in vikterna    
    def skapa_vikter_knappar(self):
        temp = self.partikelsystem.get_partikel_typ_farger()
        self.status = 'weights'
        self.knappar = []
        farg = temp[self.selected_weight]  # Hämta färgen för denna partikeltyp
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y, 100, 25, "Typ: " + self.typ_text, text_color=farg))
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + 30, 100, 25, "Vikt: " + str(self.vikter[self.selected_weight])))  # Ändrad här
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + 90, 100, 25, "+1"))
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + 120, 100, 25, "+10"))
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + 150, 100, 25, "-1"))
        self.knappar.append(Button((41, 40, 114, 50), self.x, self.y + 180, 100, 25, "-10"))
        
#    def skapa_select_weight_knappar(self):
#        self.knappar = []
#        for i, vikt in enumerate(self.vikter):
#            self.knappar.append(Button((81, 80, 214, 50), self.x, self.y + i*30, 100, 25, str(self.lista_partikel_typer[i])))
    def skapa_select_weight_knappar(self):
        self.knappar = []
        temp = self.partikelsystem.get_partikel_typ_farger()
        for i in range(len(self.vikter)):
            typ = self.lista_partikel_typer[i]  # Hämta motsvarande typ
            farg = temp[typ]  # Använd en standardfärg om typen inte finns
            self.knappar.append(Button((81, 80, 214, 50), self.x, self.y + i*30, 100, 25, str(typ), text_color=farg))  # Skicka färgen till Button
            
    def draw(self, screen):
        # Rita olika knappar beroende på status
        if self.status == 'main':
            for button in self.knappar:
                button.draw(screen)
        elif self.status == 'weights':
            for button in self.knappar:
                button.draw(screen)
        elif self.status == 'select_weight':
            for button in self.knappar:
                button.draw(screen)