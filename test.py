import pygame
import random
import math
import time
import json

TITLE = "Rogue"

WH = 800
WW = 1200

HALLWAY_WIDTH = 128

robot_sprite = pygame.image.load("robot.png")
robot_sprite = pygame.transform.scale(robot_sprite, (16, 32))

door_sprite = pygame.image.load("door.png")
#door_sprite = pygame.transform.scale(door_sprite, (16, 32))

coin_sprite = pygame.image.load("coin.png")
coin_sprite = pygame.transform.scale(coin_sprite, (16, 16))

monster_sprite = pygame.image.load("monster.png")
monster_sprite = pygame.transform.scale(monster_sprite, (32, 48))


ui_coin_sprite = pygame.image.load("coin.png")
ui_coin_sprite = pygame.transform.scale(coin_sprite, (32, 32))

is_paused = False

UP = False
DOWN = False
LEFT = False
RIGHT = False

SHOOT_UP = False
SHOOT_DOWN = False
SHOOT_LEFT = False
SHOOT_RIGHT = False

SPACE = False

ENTER = False

#these dont change between leves
level = 0
enemies_killed = 0

window = None
ingame_ui_objects = []

animation_objects = []

cam_x = 0
cam_y = 0

cam_target_x = 0
cam_target_y = 0

cam_lerp_weight = 10

#these change between leves
current_map = None
current_player = None

current_menu = None

def update_camera_position():
    global cam_y
    global cam_x
    #calculating the linear interpolation for smooth camera movement
    #pygame does have a function for this, but I wnated to learn how to do it and
    #came up with this simple calculation, so I just left it for fun
    cam_y = cam_y + ((cam_target_y-cam_y)/cam_lerp_weight)
    cam_x = cam_x + ((cam_target_x-cam_x)/cam_lerp_weight)

#UI OBJECTS
class UIObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def render(self, window):
        pass

class UIText(UIObject):
    def __init__(self, x, y, text, font, color):
        super().__init__(x, y)
        self.text = text
        self.font = font
        self.color = color

    def render(self, window):
        window.blit(self.font.render(self.text, True, self.color), (self.x, self.y))

class UISprite(UIObject):
    def __init__(self, x, y, sprite):
        super().__init__(x, y)
        self.sprite = sprite

    def render(self, window):
        window.blit(self.sprite, (self.x, self.y))

class UIRect(UIObject):
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y)
        self.w = w
        self.h = h
        self.color = color

    def render(self, window):
        pygame.draw.rect(window, self.color, (self.x, self.y, self.w, self.h))

class UILine(UIObject):
    def __init__(self, x, y, x2, y2, thickness, color):
        super().__init__(x, y)
        self.x2 = x2
        self.y2 = y2
        self.thickness = thickness
        self.color = color

    def render(self, window):
        pygame.draw.line(window, self.color, (self.x, self.y), (self.x2, self.y2), self.thickness)

class UICircle(UIObject):
    def __init__(self, x, y, r, color):
        super().__init__(x, y)
        self.r = r
        self.color = color
    def render(self, window):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.r)

class UIButton(UIObject):
    def __init__(self, x, y, w, h, text:UIText, color, selected, action_func):
        super().__init__(x, y)
        self.w = w
        self.h = h
        self.color = color
        self.selected = selected
        self.ui_text = text
        self.action_func = action_func
    def update(self):
        if self.selected:
            global ENTER
            if ENTER:
                self.action_func()
                ENTER = False

    def render(self, window):
        pygame.draw.rect(window, self.color, (self.x, self.y, self.w, self.h))
        if self.selected:
            pygame.draw.rect(window, (255, 255, 255), (self.x, self.y, self.w, self.h), 3)
        self.ui_text.render(window)

#MENUS
class Menu:
    def __init__(self):
        self.ui_objects = []
        self.buttons = []

    def update(self):
        for button in self.buttons:
            button.update()
        global SHOOT_DOWN
        global SHOOT_UP
        if SHOOT_DOWN:
            SHOOT_DOWN = False
            selected_index = [i for i in range(0, len(self.buttons)) if self.buttons[i].selected][0]

            if selected_index != len(self.buttons)-1:
                self.buttons[selected_index].selected = False
                self.buttons[selected_index+1].selected = True

        elif SHOOT_UP:
            SHOOT_UP = False
            selected_index = [i for i in range(0, len(self.buttons)) if self.buttons[i].selected][0]
            
            if selected_index != 0:
                self.buttons[selected_index].selected = False
                self.buttons[selected_index-1].selected = True

    def render(self):
        for i in self.ui_objects:
            i.render(window)
        for button in self.buttons:
            button.render(window)

class MainMenu(Menu):
    def __init__(self):
        super().__init__()

        large_arial_font = pygame.font.SysFont("Arial", 100)
        title_text = UIText(200, 150, f"Industrial Dungeons", large_arial_font, (255, 255, 255))
        self.ui_objects.append(title_text)

        pb_w = 300
        pb_h = 80
        arial_font = pygame.font.SysFont("Arial", 32)
        pb_text = UIText(WW//2-pb_w//2+120, WH//2-pb_h//2+18, "Play", arial_font, (255, 255, 255))
        self.play_btn = UIButton(WW//2-pb_w//2, 
                                WH//2-pb_h//2, 
                                pb_w, 
                                pb_h, 
                                pb_text, 
                                (30, 30, 30), 
                                True, 
                                new_game)
        self.buttons.append(self.play_btn)

        qb_w = 300
        qb_h = 80
        qb_x = WW//2-qb_w//2
        qb_y = WH//2-qb_h//2+100
        qb_text = UIText(qb_x+120, qb_y+18, "Quit", arial_font, (255, 255, 255))
        self.quit_btn = UIButton(qb_x, 
                                qb_y, 
                                qb_w, 
                                qb_h, 
                                qb_text, 
                                (30, 30, 30), 
                                False, 
                                exit)
        self.buttons.append(self.quit_btn)

class IntermissionMenu(Menu):
    def __init__(self):
        super().__init__()
        self.ui_objects.append(UICircle(30, 30, 20, (255, 255, 0)))
        arial_font = pygame.font.SysFont("Arial", 32)

        self.coin_text = UIText(55, 14, str(Player.coins), arial_font, (255, 255, 0))
        self.ui_objects.append(self.coin_text)
        self.max_health_text = UIText(10, 60, "♥"*Player.starting_health, arial_font, (255, 0, 0))
        self.ui_objects.append(self.max_health_text)

        self.damage_text = UIText(10, 90, f"Damage: {Player.damage}", arial_font, (255, 0, 0))
        self.ui_objects.append(self.damage_text)

        self.speed_text = UIText(10, 120, f"Speed: {Player.starting_speed}", arial_font, (0, 0, 255))
        self.ui_objects.append(self.speed_text)

        self.fire_rate_text = UIText(10, 150, f"Firerate: {round(Player.fire_rate, 2)}", arial_font, (255, 255, 255))
        self.ui_objects.append(self.fire_rate_text)

        self.bullet_lifetime_text = UIText(10, 180, f"Bullet Lifetime: {round(Player.bullet_lifetime, 2)}", arial_font, (255, 255, 255))
        self.ui_objects.append(self.bullet_lifetime_text)
        

        self.health_btn, self.health_cost_text = self.__generate_button(100, "Upgrade Health", 50, self.__upgrade_health, Player.level_health)

        self.damage_btn, self.damage_cost_text = self.__generate_button(200, "Upgrade Damage", 32, self.__upgrade_damage, Player.level_damage)

        self.speed_btn, self.speed_cost_text = self.__generate_button(300, "Upgrade Speed", 48, self.__upgrade_speed, Player.level_speed)

        self.firerate_btn, self.firerate_cost_text = self.__generate_button(400, "Upgrade Firerate", 40, self.__upgrade_firerate, Player.level_firerate)

        self.range_btn, self.range_cost_text = self.__generate_button(500, "Upgrade Range", 48, self.__upgrade_range, Player.level_range)

        self.continue_btn = self.__generate_button(700, "Continue", 80, load_new_map, None)

        self.buttons[0].selected = True


    def __generate_button(self, y, text, text_x, func, attribute_lvl):
        w = 300
        h = 80
        x = WW//2-w//2
        arial_font = pygame.font.SysFont("Arial", 32)

        textObj = UIText(x+text_x, y+18, text, arial_font, (255, 255, 255))
        
        btn = UIButton(x, y, w, h, textObj, (30, 30, 30), False, func)
        self.buttons.append(btn)
        if attribute_lvl == None:
            return btn
        cost_text = UIText(x+w+10, y+18, f"LEVEL: {attribute_lvl}    COST: {20+attribute_lvl*2}", arial_font, (255, 255, 0))
        self.ui_objects.append(cost_text)
        return btn, cost_text

    def remove_coins(self, amount):
        if Player.coins - amount >= 0:
            Player.coins -= amount
            self.coin_text.text = str(Player.coins)
            return True
        return False

    def __upgrade_health(self):
        if self.remove_coins((20+Player.level_health*2)):
            Player.level_health += 1
            Player.starting_health += 1
            self.max_health_text.text = "♥"*Player.starting_health
            self.health_cost_text.text = f"LEVEL: {Player.level_health}    COST: {20+Player.level_health*2}"
            print("upgraded health")

    def __upgrade_damage(self):
        if self.remove_coins((20+Player.level_damage*2)):
            Player.level_damage += 1
            Player.damage += 1
            self.damage_text.text = f"Damage: {Player.damage}"
            self.damage_cost_text.text = f"LEVEL: {Player.level_damage}    COST: {20+Player.level_damage*2}"
            print("upgraded damage")

    def __upgrade_speed(self):
        if self.remove_coins((20+Player.level_speed*2)):      
            Player.level_speed += 1
            Player.starting_speed += 0.5
            self.speed_text.text = f"Speed: {Player.starting_speed}"
            self.speed_cost_text.text = f"LEVEL: {Player.level_speed}    COST: {20+Player.level_speed*2}"
            print("upgraded speed")

    def __upgrade_firerate(self):
        if self.remove_coins((20+Player.level_firerate*2)): 
            Player.level_firerate += 1
            Player.fire_rate = pygame.math.lerp(Player.fire_rate, 0.1, 0.25)
            self.fire_rate_text.text = f"Firerate: {round(Player.fire_rate, 2)}"
            self.firerate_cost_text.text = f"LEVEL: {Player.level_firerate}    COST: {20+Player.level_firerate*2}"
            print("upgraded firerate")

    def __upgrade_range(self):
        if self.remove_coins((20+Player.level_range*2)):      
            Player.level_range += 1
            Player.bullet_lifetime += 0.2
            self.bullet_lifetime_text.text = f"Bullet Lifetime: {round(Player.bullet_lifetime, 2)}"
            self.range_cost_text.text = f"LEVEL: {Player.level_range}    COST: {20+Player.level_range*2}"
        print("upgraded range")

class DeathMenu(Menu):
    def __init__(self):
        super().__init__()

        large_arial_font = pygame.font.SysFont("Arial", 120)
        death_text = UIText(300, 150, f"YOU DIED", large_arial_font, (255, 0, 0))
        self.ui_objects.append(death_text)

        pb_w = 300
        pb_h = 80
        arial_font = pygame.font.SysFont("Arial", 32)
        pb_text = UIText(WW//2-pb_w//2+80, WH//2-pb_h//2+18, "New Game", arial_font, (255, 255, 255))
        self.play_btn = UIButton(WW//2-pb_w//2, 
                                WH//2-pb_h//2, 
                                pb_w, 
                                pb_h, 
                                pb_text, 
                                (30, 30, 30), 
                                True, 
                                new_game)
        self.buttons.append(self.play_btn)

        qb_w = 300
        qb_h = 80
        qb_x = WW//2-qb_w//2
        qb_y = WH//2-qb_h//2+100
        qb_text = UIText(qb_x+80, qb_y+18, "Main Menu", arial_font, (255, 255, 255))
        self.quit_btn = UIButton(qb_x, 
                                qb_y, 
                                qb_w, 
                                qb_h, 
                                qb_text, 
                                (30, 30, 30), 
                                False, 
                                lambda: load_menu(MainMenu()))
        self.buttons.append(self.quit_btn)

#ANIMATIONS
class AnimObject:
    def __init__(self, length, animation_list):
        self.start_time = time.time()
        self.length = length
        self.animation_list = animation_list
    
    def animate(self, window):
        if time.time()-self.start_time >= self.length:
            self.animation_list.remove(self)

class DamageAnim(AnimObject):
    def __init__(self, length, animation_list, color, parent):
        super().__init__(length, animation_list)
        self.x = parent.x
        self.y = parent.y
        self.w = parent.collider.width
        self.h = parent.collider.height
        self.parent = parent

        self.color = color
        self.rect = pygame.Surface((self.w, self.h))  # the size of your rect
        self.rect.fill(self.color) 
        self.sinx = 1

    def animate(self, window):
        super().animate(window)
        self.x = self.parent.x
        self.y = self.parent.y
        self.sinx += 0.3
        self.rect.set_alpha((math.sin(self.sinx)+1)*128)
        window.blit(self.rect, ((-cam_x+WW/2) + (self.x-self.w/2), (-cam_y+WH/2) + (self.y-self.h/2)))


#INGAME OBJECTS
class GameObject:
    def __init__(self, x, y, sprite, room):
        self.x = x
        self.y = y
        self.current_room = room
        self.sprite = sprite
        self.collider = None
        self.last_collider = None

        if self.sprite != None:
            self.collider = pygame.Rect((-cam_x+WW/2)+self.x-self.sprite.get_width()/2, (-cam_y+WH/2)+self.y-self.sprite.get_height()/2, self.sprite.get_width(), self.sprite.get_height())
    
    def update(self, window):
        if self.collider != None:
            self.collider.update((-cam_x+WW/2)+self.x-self.collider.width/2, (-cam_y+WH/2)+self.y-self.collider.height/2, self.collider.width, self.collider.height)

    def update_collision(self):
        pass
    #Returns true if object went out of bounds druing movement
    def move(self, x, y):
        #checking if the object crossed the room border and teleport him back instantly
        #this is because the movement is updated with pixel, so the player could cross it by a few pixels
        #even if we checked it earlier
        #i did the movement boundary check in this order because it was the easiest to write and also understand

        self.x = x
        self.y = y
        room_top = int(self.current_room.y-(self.current_room.h/2))
        room_bottom = int(self.current_room.y+(self.current_room.h/2))
        room_left = int(self.current_room.x-(self.current_room.w/2))
        room_right = int(self.current_room.x+(self.current_room.w/2))

        out = False
        if self.y-self.collider.height/2 < room_top: self.y = int(room_top+self.collider.height/2); out = True
        if self.y+self.collider.height/2 > room_bottom: self.y = int(room_bottom-self.collider.height/2); out = True
        if self.x-self.collider.width/2 < room_left: self.x = int(room_left+self.collider.width/2); out = True
        if self.x+self.collider.width/2 > room_right: self.x = int(room_right-self.collider.width/2); out = True
        return out
    
    def render(self, window):
        if self.sprite == None:
            return
        window.blit(self.sprite, ((-cam_x+WW/2) + (self.x-self.sprite.get_width()/2), (-cam_y+WH/2) + (self.y-self.sprite.get_height()/2) ))
        #DEBUGGING
        #pygame.draw.rect(window, (255, 0, 0), self.collider, 1)

class Door(GameObject):
    def __init__(self, x, y, hallway, direction, room):
        super().__init__(x, y, door_sprite, room)
        self.hallway = hallway
        self.direction = direction
        self.collider.width = 5
        self.collider.height = 5
        self.is_animating = False
        self.next_point = self.hallway.points[0]
        if self.direction == -1:
            self.next_point = self.hallway.points[-1]
        self.player = None

    def enter(self, player):
        global is_paused
        is_paused = True
        self.is_animating = True
        self.player = player
        
        
    def update(self, window):
        super().update(window)
        if not self.is_animating:
            return
        self.player.x = pygame.math.lerp(self.player.x, self.next_point[1], 0.1)
        self.player.y = pygame.math.lerp(self.player.y, self.next_point[0], 0.1)
        if math.dist((self.player.x, self.player.y), (self.next_point[1], self.next_point[0])) < 3:
            self.player.x = self.next_point[1]
            self.player.y = self.next_point[0]

        global cam_target_x
        global cam_target_y
        cam_target_x = self.player.x
        cam_target_y = self.player.y

        points = self.hallway.points.copy()
        if self.direction == -1:
            points.reverse()

        if int(self.player.x) == int(self.next_point[1]) and int(self.player.y) == int(self.next_point[0]):
            if self.next_point != points[-1]:
                self.next_point = points[points.index(self.next_point)+1]
            else:
                x_offset = 0
                y_offset = self.player.collider.height

                if self.hallway.direction == "x":
                    x_offset = self.player.collider.width
                    y_offset = 0
                global is_paused
                is_paused = False
                if self.direction == 1:
                    self.player.start_invincibility()
                    self.player.current_room = self.hallway.room2
                    self.player.move(self.player.x+x_offset, self.player.y+y_offset)
                    

                if self.direction == -1:
                    self.player.start_invincibility()
                    self.player.current_room = self.hallway.room1
                    self.player.move(self.player.x-x_offset, self.player.y-y_offset)
                    
                
                self.is_animating = False
                self.next_point = points[0]

    #this render function is just here to override the GameObject render, 
    # because halfway through I realised it looks better without the door sprites
    # But didn't wan't to revamp the whole GameObject and all its children
    def render(self, window):
        pygame.draw.circle(window, (255, 255, 255), ((-cam_x+WW/2) + self.x, (-cam_y+WH/2)+ self.y), 8)

class Elevator(GameObject):
    def __init__(self, x, y, room):
        super().__init__(x, y, door_sprite, room)

    def enter(self):
        load_menu(IntermissionMenu())

class Coin(GameObject):
    def __init__(self, x, y, room):
        super().__init__(x, y, coin_sprite, room)
    def update(self, window):
        super().update(window)

class Enemy(GameObject):
    def __init__(self, x, y, room):
        super().__init__(x, y, monster_sprite, room)
        self.health = random.randint(2, level+1)
        self.target_x = self.x
        self.target_y = self.y
        self.x_offset = math.cos(random.randint(1, 20)/math.pi*2)*random.randint(40, 140)
        self.y_offset = math.sin(random.randint(1, 20)/math.pi*2)*random.randint(40, 140)
        self.__near_player = False
        self.last_attack_time = time.time()
        self.attack_rate = 1.0
        self.damage = 1
        self.speed = random.uniform(0.4, 1+(level/5))
    def take_damage(self):
        global animation_objects
        animation_objects.append(DamageAnim(0.3, animation_objects, (255, 0, 0), self))
        self.health -= Player.damage
        if self.health <= 0:
            self.die()
    def die(self):
        global enemies_killed
        enemies_killed += 1
        self.current_room.gameobjects.remove(self)
    
    def update(self, window):
        super().update(window)
        if not self.__near_player:
            self.target_x = current_player.x + self.x_offset
            self.target_y = current_player.y + self.y_offset
        else:
            self.target_x = current_player.x
            self.target_y = current_player.y
            self.x_offset = math.cos(random.randint(1, 20)/math.pi*2)*random.randint(40, 140)
            self.y_offset = math.sin(random.randint(1, 20)/math.pi*2)*random.randint(40, 140)
        self.__movement()
        range = 8
        if abs(self.target_x - self.x) < range and abs(self.target_y - self.y) < range:
            self.__near_player = not self.__near_player
        self.__do_damage()
        
    def __do_damage(self):
        if time.time()-self.last_attack_time > self.attack_rate:
            if pygame.Rect.colliderect(self.collider, current_player.collider):
                current_player.take_damage(self.damage)
                self.last_attack_time = time.time()
    def __movement(self):
        if self.x == current_player.x and self.y == current_player.y: return
        direction = [0, 0]
        x_dif = self.target_x - self.x
        y_dif = self.target_y - self.y

        if x_dif > 1: direction[1] = 1
        elif x_dif < 1: direction[1] = -1
        if y_dif > 1: direction[0] = 1
        elif y_dif < 1: direction[0] = -1
        went_out_of_bounds = self.move(self.x + (direction[1]*self.speed), self.y + (direction[0]*self.speed))
        if went_out_of_bounds:
            self.x_offset = -self.x_offset
            self.y_offset = -self.y_offset

class Bullet(GameObject):
    def __init__(self, x, y, room, direction):
        super().__init__(x, y, coin_sprite, room)
        self.direction = direction
        self.__spawn_time = time.time()
    def update(self, window):
        super().update(window)
        went_out_of_bounds = self.move(self.x+self.direction[1]*Player.bullet_speed,
        self.y+self.direction[0]*Player.bullet_speed)
        if went_out_of_bounds or time.time()-self.__spawn_time > Player.bullet_lifetime:
            self.destroy_self()
            
    def update_collision(self):
        for i in self.current_room.gameobjects:
            if isinstance(i, Enemy) and pygame.Rect.colliderect(self.collider, i.collider):
                i.take_damage()
                self.destroy_self()
                return

    def render(self, window):
        pygame.draw.circle(window, (255, 0, 0), ((-cam_x+WW/2) + self.x, (-cam_y+WH/2)+ self.y), 5)
    def destroy_self(self):
        self.current_room.gameobjects.remove(self)

class Player(GameObject):

    coins = 0

    level_health = 1
    level_damage = 1
    level_speed = 1
    level_firerate = 1
    level_range = 1

    starting_speed = 5
    starting_health = 2
    damage = 1
    #therange is the lifetime of the bulletin seconds
    bullet_lifetime = 0.15
    bullet_speed = 10
    fire_rate = 1.0

    

    def __init__(self, x, y, room, room_count):
        super().__init__(x, y, robot_sprite, room)

        global current_player
        current_player = self
        self.speed = Player.starting_speed
        self.health = Player.starting_health
        self.invicible = False
        self.invincibility_start_time = 0

        self.__last_shot_time = time.time()

        global ingame_ui_objects
        ingame_ui_objects.append(UICircle(30, 30, 20, (255, 255, 0)))
        arial_font = pygame.font.SysFont("Arial", 32)

        self.coin_text = UIText(55, 14, f"{Player.coins}", arial_font, (255, 255, 0))
        ingame_ui_objects.append(self.coin_text)

        self.max_health_text = UIText(10, 60, "♡"*Player.starting_health, arial_font, (255, 0, 0))
        ingame_ui_objects.append(self.max_health_text)
        self.health_text = UIText(10, 60, "♥"*self.health, arial_font, (255, 0, 0))
        ingame_ui_objects.append(self.health_text)

        self.damage_text = UIText(10, 90, f"Damage: {Player.damage}", arial_font, (255, 0, 0))
        ingame_ui_objects.append(self.damage_text)

        self.speed_text = UIText(10, 120, f"Speed: {Player.starting_speed}", arial_font, (0, 0, 255))
        ingame_ui_objects.append(self.speed_text)

        self.fire_rate_text = UIText(10, 150, f"Firerate: {round(Player.fire_rate, 2)}", arial_font, (255, 255, 255))
        ingame_ui_objects.append(self.fire_rate_text)

        self.bullet_lifetime_text = UIText(10, 180, f"Bullet Lifetime: {round(Player.bullet_lifetime, 2)}", arial_font, (255, 255, 255))
        ingame_ui_objects.append(self.bullet_lifetime_text)
        

    def update(self, window):
        super().update(window)
        if is_paused: return
        self.__movement()
        self.__collision()
        if time.time()-self.__last_shot_time >= Player.fire_rate:
            self.__shoot()
        
    def update_collision(self):
        self.__collision()

    def __collision(self):
        for i in self.current_room.gameobjects:
            if pygame.Rect.colliderect(self.collider, i.collider):
                if isinstance(i, Coin):
                    self.__collect_coin(i)
                elif isinstance(i, Door) and SPACE:
                    if self.last_collider != i.collider:
                        i.enter(self)
                elif isinstance(i, Elevator) and SPACE:
                    if self.last_collider != i.collider:
                        i.enter()
                self.last_collider = i
    def __movement(self):
        direction = [0, 0]

        #getting input direction
        if UP: direction[0] = -1
        if DOWN: direction[0] = 1
        if LEFT: direction[1] = -1
        if RIGHT: direction[1] = 1

        #normalizing direction so diagonal movement isnt faster
        move = pygame.math.Vector2(direction[1], direction[0])
        if move.length_squared() > 0:
            move.scale_to_length(self.speed)
            self.move(self.x + round(move.x), self.y + round(move.y))

        global cam_target_y
        global cam_target_x
        cam_target_y = self.y
        cam_target_x = self.x

    def __shoot(self):
        if not SHOOT_UP and not SHOOT_DOWN and not SHOOT_LEFT and not SHOOT_RIGHT: return
        bullet = Bullet(self.x, self.y, self.current_room, [0, 0])
        if SHOOT_UP: bullet.direction = [-1, 0]
        if SHOOT_DOWN: bullet.direction = [1, 0]
        if SHOOT_LEFT: bullet.direction = [0, -1]
        if SHOOT_RIGHT: bullet.direction = [0, 1]
        self.current_room.gameobjects.append(bullet)
        self.__last_shot_time = time.time()

    def start_invincibility(self):
        self.invincibility_start_time = time.time()
        #we use the damaganim but in white to signal invincibility
        global animation_objects
        #1.5 is the time the player is invincible
        animation_objects.append(DamageAnim(1.5, animation_objects, (255, 255, 255), self))

    def take_damage(self, amount):
        if time.time()-self.invincibility_start_time < 1.5: return

        global animation_objects
        animation_objects.append(DamageAnim(0.3, animation_objects, (255, 0, 0), self))
        self.health -= amount
        self.health_text.text = str("♥"*self.health)
        if self.health <= 0:
            self.die()
    def die(self):
        load_menu(DeathMenu())
    def __collect_coin(self, coin):
        Player.coins += 1
        self.current_room.gameobjects.remove(coin)
        self.coin_text.text = f"{Player.coins}"

class Room:
    def __init__(self, location, is_first):
        self.location = location
        self.w = random.randint(300, 800)
        self.h = random.randint(200, 700)

        self.y = (location[0]*1000)+random.randint(self.h//2, 900-self.h//2)
        self.x = (location[1]*1000)+random.randint(self.w//2, 900-self.w//2)

        self.gameobjects = []
        self.gameobjects.append(Coin(self.x, self.y, self))
        for i in range(0, random.randint(2, pygame.math.clamp(level, 5, 8))):
            temp_coin = Coin(self.x, self.y, self)
            temp_coin.x = random.randint((self.x-self.w//2)+(temp_coin.collider.w//2), (self.x+self.w//2)-(temp_coin.collider.w//2))
            temp_coin.y = random.randint((self.y-self.h//2)+(temp_coin.collider.h//2), (self.y+self.h//2)-(temp_coin.collider.h//2))
            self.gameobjects.append(temp_coin)

        if not is_first:
            for i in range(0, random.randint(2, pygame.math.clamp(level, 5, 8))):
                temp_enemy = Enemy(self.x, self.y, self)
                temp_enemy.x = random.randint((self.x-self.w//2)+(temp_enemy.collider.w//2), (self.x+self.w//2)-(temp_enemy.collider.w//2))
                temp_enemy.y = random.randint((self.y-self.h//2)+(temp_enemy.collider.h//2), (self.y+self.h//2)-(temp_enemy.collider.h//2))
                self.gameobjects.append(temp_enemy)
        #DEBUGGIN
        #self.gameobjects.append(Elevator(self.x, self.y, self))

    def update(self, window):
        for gameobject in self.gameobjects:
            gameobject.update(window)
    def update_collision(self):
        for gameobject in self.gameobjects:
            gameobject.update_collision()
    def render(self, window):
        pygame.draw.rect(window, (30, 30, 30), ((-cam_x+WW/2) + (self.x-self.w/2),\
                                                (-cam_y+WH/2) + (self.y-self.h/2), self.w, self.h))
        for gameobject in self.gameobjects:
            gameobject.render(window)

    def render_outline(self, window):
        pygame.draw.rect(window, (255, 255, 255), 
                        (((-cam_x+WW/2) + (self.x-self.w/2))-3,
                        ((-cam_y+WH/2) + (self.y-self.h/2))-3, 
                        self.w+6, self.h+6), 3)

class Hallway:
    def __init__(self, room1, room2):
        self.room1 = room1
        self.room2 = room2
        self.point1, self.point2, self.direction = self.__find_points_on_sides()

        self.points = [self.point1]

        if self.direction == "x":
            self.points.append([self.point1[0], self.point1[1] + ((self.point2[1]-self.point1[1])/2)])
        else:
            self.points.append([self.point1[0] + ((self.point2[0]-self.point1[0])/2), self.point1[1]])
        
        if self.direction == "x":
            self.points.append([self.point2[0], self.points[-1][1]])
        else:
            self.points.append([self.points[-1][0], self.point2[1]])

        self.points.append(self.point2)
    

    def __find_points_on_sides(self):
        point1 = [0, 0]
        point2 = [0, 0]
        direction = "y"
        if self.room1.location[1] == self.room2.location[1]:
            point1 = [self.room1.y + self.room1.h/2, random.randint(int((self.room1.x-self.room1.w/2) + HALLWAY_WIDTH/2), 
                            int((self.room1.x+self.room1.w/2) - HALLWAY_WIDTH/2))]
            point2 = [self.room2.y - self.room2.h/2, random.randint(int((self.room2.x-self.room2.w/2) + HALLWAY_WIDTH/2), 
                            int((self.room2.x+self.room2.w/2) - HALLWAY_WIDTH/2))]
            #fix some bug when the points are exactly against eachother
            if point1[0] == point2[0]:
                point1[0]+=10
                point2[0] -=10
            direction = "y"
        else:
            point1 = [random.randint(int((self.room1.y-self.room1.h/2) + HALLWAY_WIDTH/2), int((self.room1.y+self.room1.h/2) - HALLWAY_WIDTH/2)), self.room1.x + self.room1.w/2]
            point2 = [random.randint(int((self.room2.y-self.room2.h/2) + HALLWAY_WIDTH/2), int((self.room2.y+self.room2.h/2) - HALLWAY_WIDTH/2)), self.room2.x - self.room2.w/2]
            direction = "x"
            #fix some bug when the points are exactly against eachother
            if point1[1] == point2[1]:
                point1[1]+=10
                point2[1] -=10
        return point1, point2, direction

    def render(self, window):
        for i in range(0, len(self.points)-1):
            pygame.draw.line(window, (155, 155, 0), ((-cam_x+WW/2) + (self.points[i][1]),(-cam_y+WH/2) + (self.points[i][0])),\
                                                ((-cam_x+WW/2) + (self.points[i+1][1]),(-cam_y+WH/2) + (self.points[i+1][0])), 2)
            
class Map:
    def __init__(self, window):


        self.__update_level_counter()


        self.window = window
        self.gameobjects = []
        self.rooms = []
        self.hallways = []

        self.__generate_rooms()
        self.__generate_hallways()

        elevator_room = random.choice(self.rooms)
        elevator_room.gameobjects.insert(0, Elevator(elevator_room.x, elevator_room.y, elevator_room))
        self.player = Player(self.rooms[0].x-(self.rooms[0].w/2)+30, self.rooms[0].y-(self.rooms[0].h/2)+50, self.rooms[0], len(self.rooms))


    def __update_level_counter(self):
        global level
        level += 1
        arial_font = pygame.font.SysFont("Arial", 24)

        count_str = "th"
        if level == 2:
            count_str = "nd"
        elif level == 3:
            count_str = "rd"
        string = f"{level}{count_str} Floor"
        text = UIText(WW-arial_font.size(string)[0]-20, 0, string, arial_font, (255, 0, 0))
        
        global ingame_ui_objects
        ingame_ui_objects.append(text)

    def __generate_rooms(self):
        is_first = True
        for y in range(0, 4):
            for x in range(0, 4):
                if random.randint(0, 4) != 1:
                    self.rooms.append(Room((y, x), is_first))
                    is_first = False
                elif x > 1 and y > 1 and len([1 for i in self.rooms if i.location[1] == x]) < 2 and len([1 for i in self.rooms if i.location[1] == x]) < 2:
                    self.rooms.append(Room((y, x), is_first))
                    is_first = False
                

    def __generate_hallways(self):
        for room in self.rooms:
            close_rooms = []
            for m in range(0, 4):
                for i in self.rooms:
                    if i.location[0] == room.location[0]+m+1 and i.location[1] == room.location[1]:
                        close_rooms.append(i)
                    elif i.location[1] == room.location[1]+m+1 and i.location[0] == room.location[0]:
                        close_rooms.append(i)
                if len(close_rooms) != 0:
                    break
            for i in close_rooms:
                temp_hallway = Hallway(room, i)
                self.hallways.append(temp_hallway)
                room.gameobjects.append(Door(temp_hallway.point1[1], temp_hallway.point1[0], temp_hallway, 1, room))
                i.gameobjects.append(Door(temp_hallway.point2[1], temp_hallway.point2[0], temp_hallway, -1, i))

    def update(self):
        self.player.update(self.window)
        #we update the camera position before updating other positions
        #because the other position are relaing on the cameras position

        update_camera_position()
        self.player.current_room.update(self.window)
        

    def update_collision(self):
        self.player.update_collision()
        self.player.current_room.update_collision()


    def render(self):
        #DEBBUGING RECTANGLES
        # for y in range(0, 4):
        #     for x in range(0, 4):
        #         pygame.draw.rect(self.window, (255, 255, 255), \
        #                                 ((-cam_x+WW/2) + (1000*x),\
        #                                 (-cam_y+WH/2) + (1000*y), 1000, 1000), 3)
        for hallway in self.hallways:
            hallway.render(self.window)

        self.player.current_room.render(self.window)
        self.player.render(self.window)

        for i in animation_objects:
            i.animate(self.window)
        

        for room in self.rooms:
            room.render_outline(self.window)


def load_menu(menu):
    global current_map
    current_map = None
    global current_menu
    current_menu = menu
    global ingame_ui_objects
    ingame_ui_objects.clear()
    
def new_game():
    Player.coins = 0

    Player.level_health = 1
    Player.level_damage = 1
    Player.level_speed = 1
    Player.level_firerate = 1
    Player.level_range = 1

    Player.starting_speed = 5
    Player.starting_health = 2
    Player.damage = 1
    #therange is the lifetime of the bulletin seconds
    Player.bullet_lifetime = 0.15
    Player.bullet_speed = 10
    Player.fire_rate = 1.0

    enemies_killed = 0

    load_new_map()

def load_new_map():
    global current_menu
    current_menu = None
    global ingame_ui_objects
    ingame_ui_objects.clear()
    global current_map
    current_map = Map(window)

def gather_input():
    global UP
    global DOWN
    global LEFT
    global RIGHT
    global SPACE
    global SHOOT_UP
    global SHOOT_DOWN
    global SHOOT_LEFT
    global SHOOT_RIGHT
    global ENTER
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                LEFT = True
            if event.key == pygame.K_d:
                RIGHT = True
            if event.key == pygame.K_w:
                UP = True
            if event.key == pygame.K_s:
                DOWN = True
            if event.key == pygame.K_SPACE:
                SPACE = True
            
            if event.key == pygame.K_RETURN:
                ENTER = True

            if event.key == pygame.K_LEFT:
                SHOOT_LEFT = True
            elif event.key == pygame.K_RIGHT:
                SHOOT_RIGHT = True
            elif event.key == pygame.K_UP:
                SHOOT_UP = True
            elif event.key == pygame.K_DOWN:
                SHOOT_DOWN = True
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                LEFT = False
            if event.key == pygame.K_d:
                RIGHT = False
            if event.key == pygame.K_w:
                UP = False
            if event.key == pygame.K_s:
                DOWN = False
            if event.key == pygame.K_SPACE:
                SPACE = False

            if event.key == pygame.K_RETURN:
                ENTER = False

            if event.key == pygame.K_LEFT:
                SHOOT_LEFT = False
            elif event.key == pygame.K_RIGHT:
                SHOOT_RIGHT = False
            elif event.key == pygame.K_UP:
                SHOOT_UP = False
            elif event.key == pygame.K_DOWN:
                SHOOT_DOWN = False
        if event.type == pygame.QUIT:
            exit()

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    global window
    flags = pygame.FULLSCREEN | pygame.SCALED
    window = pygame.display.set_mode((WW, WH), flags)

    clock = pygame.time.Clock()

    #global current_map
    #current_map = Map(window)
    load_menu(MainMenu())
    while True:
        
        gather_input()
        
        #we only update the menu if its open
        if current_menu != None:
            current_menu.update()
            window.fill((0, 0, 0))

            try: current_menu.render()
            except: pass
            pygame.display.flip()

            clock.tick(60)
            continue

        current_map.update()
        try:current_map.update_collision()
        except: pass

        window.fill((14, 1, 15))

        try:current_map.render()
        except: pass

        global ingame_ui_objects
        for i in ingame_ui_objects:
            i.render(window)
        pygame.display.flip()

        clock.tick(60)




if __name__ == "__main__":
    main()