import pygame
import random
import math

TITLE = "Rogue"

WH = 600
WW = 800

HALLWAY_WIDTH = 128

robot_sprite = pygame.image.load("robot.png")
robot_sprite = pygame.transform.scale(robot_sprite, (16, 32))

door_sprite = pygame.image.load("door.png")
door_sprite = pygame.transform.scale(door_sprite, (16, 32))

coin_sprite = pygame.image.load("coin.png")
coin_sprite = pygame.transform.scale(coin_sprite, (16, 16))
monster_sprite = pygame.image.load("monster.png")

is_paused = False

UP = False
DOWN = False
LEFT = False
RIGHT = False
SPACE = False

level = 0
window = None
current_map = None

ingame_ui_objects = []

cam_x = 0
cam_y = 0

cam_target_x = 0
cam_target_y = 0

cam_lerp_weight = 10

def update_camera_position():
    global cam_y
    global cam_x
    #calculating the linear interpolation for smooth camera movement
    #pygame does have a function for this, but I wnated to learn how to do it and
    #came up with this simple calculation, so I just left it for fun
    cam_y = cam_y + ((cam_target_y-cam_y)/cam_lerp_weight)
    cam_x = cam_x + ((cam_target_x-cam_x)/cam_lerp_weight)


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

        if self.y-self.collider.height/2 < room_top: self.y = int(room_top+self.collider.height/2)
        if self.y+self.collider.height/2 > room_bottom: self.y = int(room_bottom-self.collider.height/2)
        if self.x-self.collider.width/2 < room_left: self.x = int(room_left+self.collider.width/2)
        if self.x+self.collider.width/2 > room_right: self.x = int(room_right-self.collider.width/2)
    
    def render(self, window):
        if self.sprite == None:
            return
        window.blit(self.sprite, ((-cam_x+WW/2) + (self.x-self.sprite.get_width()/2), (-cam_y+WH/2) + (self.y-self.sprite.get_height()/2) ))
        #DEBUGGING
        pygame.draw.rect(window, (255, 0, 0), self.collider, 1)

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
        print("hi")
        self.player.x = pygame.math.lerp(self.player.x, self.next_point[1], 0.1)
        self.player.y = pygame.math.lerp(self.player.y, self.next_point[0], 0.1)
        if math.dist((self.player.x, self.player.y), (self.next_point[1], self.next_point[0])) < 3:
            self.player.x = self.next_point[1]
            self.player.y = self.next_point[0]

        global cam_target_x
        global cam_target_y
        cam_target_x = self.player.x
        cam_target_y = self.player.y

        print(int(self.player.x), int(self.player.y), int(self.next_point[1]), int(self.next_point[0]))
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
                    self.player.current_room = self.hallway.room2
                    self.player.move(self.player.x+x_offset, self.player.y+y_offset)
                    

                if self.direction == -1:
                    self.player.current_room = self.hallway.room1
                    self.player.move(self.player.x-x_offset, self.player.y-y_offset)
                    
                
                self.is_animating = False
                self.next_point = points[0]

    #this render function is just here to override the GameObject render, 
    # because halfway through I realised it looks better without the door sprites
    # But didn't wan't to revamp the whole GameObject and all its children
    def render(self, window):
        pygame.draw.circle(window, (255, 255, 255), ((-cam_x+WW/2) + self.x, (-cam_y+WH/2)+ self.y), 8)

class Coin(GameObject):
    def __init__(self, x, y, room):
        super().__init__(x, y, coin_sprite, room)
    def update(self, window):
        super().update(window)
    def render(self, window):
        super().render(window)

class Player(GameObject):
    def __init__(self, x, y, room, room_count):
        super().__init__(x, y, robot_sprite, room)
        self.speed = 10
        self.max_coins = room_count
        self.coins = 0

        arial_font = pygame.font.SysFont("Arial", 24)
        self.text = UIText(20, 0, f"{self.coins}/{self.max_coins} Coins Collected", arial_font, (255, 255, 0))
        global ingame_ui_objects
        ingame_ui_objects.append(self.text)

    def update(self, window):
        super().update(window)
        if is_paused: return
        self.__movement()
        self.__collision()

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
                        print("It's Door")
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


    def __collect_coin(self, coin):
        self.coins += 1
        self.current_room.gameobjects.remove(coin)
        self.text.text = f"{self.coins}/{self.max_coins} Coins Collected"
        if self.coins >= self.max_coins:
            load_new_map()

class Room:
    def __init__(self, location):
        self.location = location
        self.w = random.randint(300, 800)
        self.h = random.randint(200, 700)

        self.y = (location[0]*1000)+random.randint(self.h//2, 900-self.h//2)
        self.x = (location[1]*1000)+random.randint(self.w//2, 900-self.w//2)

        self.gameobjects = []
        self.gameobjects.append(Coin(self.x, self.y, self))

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
            direction = "y"
        else:
            point1 = [random.randint(int((self.room1.y-self.room1.h/2) + HALLWAY_WIDTH/2), int((self.room1.y+self.room1.h/2) - HALLWAY_WIDTH/2)), self.room1.x + self.room1.w/2]
            point2 = [random.randint(int((self.room2.y-self.room2.h/2) + HALLWAY_WIDTH/2), int((self.room2.y+self.room2.h/2) - HALLWAY_WIDTH/2)), self.room2.x - self.room2.w/2]
            direction = "x"
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
        for y in range(0, 4):
            for x in range(0, 4):
                if random.randint(0, 4) != 1:
                    self.rooms.append(Room((y, x)))
                elif x > 1 and y > 1 and len([1 for i in self.rooms if i.location[1] == x]) < 2 and len([1 for i in self.rooms if i.location[1] == x]) < 2:
                    self.rooms.append(Room((y, x)))

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

        

        for room in self.rooms:
            room.render_outline(self.window)

        

def load_new_map():
    global ingame_ui_objects
    ingame_ui_objects.clear()
    global current_map
    current_map = Map(window)


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    global window
    window = pygame.display.set_mode((WW, WH))

    clock = pygame.time.Clock()


    global UP
    global DOWN
    global LEFT
    global RIGHT
    global SPACE

    global current_map
    current_map = Map(window)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    LEFT = True
                if event.key == pygame.K_RIGHT:
                    RIGHT = True
                if event.key == pygame.K_UP:
                    UP = True
                if event.key == pygame.K_DOWN:
                    DOWN = True
                if event.key == pygame.K_SPACE:
                    SPACE = True
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    LEFT = False
                if event.key == pygame.K_RIGHT:
                    RIGHT = False
                if event.key == pygame.K_UP:
                    UP = False
                if event.key == pygame.K_DOWN:
                    DOWN = False
                if event.key == pygame.K_SPACE:
                    SPACE = False
            if event.type == pygame.QUIT:
                exit()
            
        
        current_map.update()

        current_map.update_collision()

        window.fill((0, 0, 0))
        current_map.render()

        global ingame_ui_objects
        for i in ingame_ui_objects:
            i.render(window)
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()