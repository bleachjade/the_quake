import arcade.key
import sys
from random import randint, random
from crash_detect import check_crash
import time
import math
import pyglet
# pyglet.options['audio'] = ('openal', 'pulse', 'directsound', 'silent',)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

GRAVITY = -1
MAX_VX = 13
ACCX = 1
JUMP_VY = 15

DOT_RADIUS = 40
BUILDING_MARGIN = 5

ITEM_RADIUS = 32
ITEM_Y_OFFSET = 25
ITEM_MARGIN = 13
ITEM_HIT_MARGIN = 30

BULLET_RADIUS = 30
BULLET_Y_OFFSET = 23
BULLET_MARGIN = 12
BULLET_HIT_MARGIN = 28

class Model:
    def __init__(self, world, x, y, angle):
        self.world = world
        self.x = x
        self.y = y
        self.angle = 0


class Player(Model):
    def __init__(self, world, x, y):
        super().__init__(world, x, y, 0)
        self.vx = 0
        self.vy = 0
        self.is_jump = False

        self.platform = None

        self.status = False

    def jump(self):
        if not self.building:
            return

        if not self.is_jump:
            self.is_jump = True
            self.vy = JUMP_VY
            arcade.sound.play_sound(self.world.jump_sound)

    def update(self, delta):
        self.die()
        if self.vx < MAX_VX:
            self.vx += ACCX

        self.x += self.vx

        if self.is_jump:
            self.y += self.vy
            self.vy += GRAVITY

            new_building = self.find_touching_building()
            if new_building:
                self.vy = 0
                self.set_building(new_building)
        else:
            if (self.building) and (not self.is_on_building(self.building)):
                self.building = None
                self.is_jump = True
                self.vy = 0
    def top_y(self):
        return self.y + (DOT_RADIUS // 2)

    def bottom_y(self):
        return self.y - (DOT_RADIUS // 2)

    def set_building(self, building):
        self.is_jump = False
        self.building = building
        self.y = building.y + (DOT_RADIUS // 2)

    def is_on_building(self, building, margin=BUILDING_MARGIN):
        if not building.in_top_range(self.x):
            return False

        if abs(building.y - self.bottom_y()) <= BUILDING_MARGIN:
            return True

        return False

    def is_falling_on_building(self, building):
        if not building.in_top_range(self.x):
            return False

        if self.bottom_y() - self.vy > building.y > self.bottom_y():
            return True

        return False

    def find_touching_building(self):
        building = self.world.building
        for b in building:
            if self.is_falling_on_building(b):
                return b
        return None

    def die(self):
        if self.top_y() < 0:
            # print('yay')
            # self.world.die()
            self.world.state = 3
            # arcade.sound.play_sound(self.world.death_sound)
            return True
        return False

class Building:
    def __init__(self, world, x, y, width, height):
        self.world = world
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def in_top_range(self, x):
        return self.x <= x <= self.x + self.width

    def right_most_x(self):
        return self.x + self.width

    def spawn_items(self):
        items = []
        x = self.x + ITEM_MARGIN
        while x + ITEM_MARGIN <= self.right_most_x():
            items.append(Item(x, self.y + ITEM_Y_OFFSET,
                              ITEM_RADIUS, ITEM_RADIUS))
            x += ITEM_MARGIN + ITEM_RADIUS
        return items
    # def spawn_bullets(self):
    #     bullets = []
    #     x = self.x + BULLET_MARGIN
    #     while x + BULLET_MARGIN <= self.right_most_x():
    #         bullets.append(Item(x, self.y + BULLET_Y_OFFSET,
    #                           BULLET_RADIUS, BULLET_RADIUS))
    #         x += BULLET_MARGIN + BULLET_RADIUS
    #     return bullets

class Item:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_collected = False
        self.effect = False
        if random() > 0.986:
            self.effect = True

    def hit(self, player):
        return ((abs(self.x - player.x) < ITEM_HIT_MARGIN) and
                (abs(self.y - player.y) < ITEM_HIT_MARGIN))

class Bullet:
    def __init__(self, world, x, y):
        self.world = world
        self.x = x
        self.y = y
        self.is_hit = False
        self.speed = 1

    def hit(self, player):
        return check_crash(player.x, player.y, self.x, self.y)

    # def hit_bul(self, player):
    #     return ((abs(self.x - player.x) < BULLET_HIT_MARGIN) and
    #             (abs(self.y - player.y) < BULLET_HIT_MARGIN))

    def update(self):
        # for i in SCREEN_HEIGHT:
            if (self.x < self.world.player.x-400):
                self.x = self.world.player.x+420
                self.y = randint(50, SCREEN_HEIGHT - 50)
            self.x -= self.speed

class World:
    STATE_FROZEN = 1
    STATE_STARTED = 2
    STATE_DEAD = 3

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.player = Player(self, 0, 120)
        self.init_building()

        self.player.set_building(self.building[0])

        self.score = 0

        self.state = World.STATE_FROZEN

        self.status = False

        self.bullet = Bullet(self, SCREEN_WIDTH - 1, randint(50, SCREEN_HEIGHT - 50))
        self.bullet_list = []

        self.jump_sound = arcade.sound.load_sound('sound/jump1.wav')
        self.death_sound = arcade.sound.load_sound('sound/death.wav')
        # self.bg = arcade.sound.load_sound('sound/Electronic-beat.mp3')

    def init_building(self):
        self.building = [
            Building(self, 0, 100, 500, 50),
            Building(self, 550, 150, 500, 50),
            Building(self, 1100, 100, 500, 50),
        ]
        self.items = []
        # self.bullets = []
        for b in self.building:
            self.items += b.spawn_items()

    def update(self, delta):
        if self.state in [World.STATE_FROZEN, World.STATE_DEAD]:
            return
        self.player.update(delta)
        self.bullet.update()
        self.recycle_building()
        self.collect_items()
        self.remove_old_items()
        for bullet in self.bullet_list:
            bullet.update(delta)
            if bullet.hit(self.player):
                self.die()
        # self.hit_bullet()
        # self.remove_old_bullet()

    def collect_items(self):
        for i in self.items:
            if (not i.is_collected) and (i.hit(self.player)):
                i.is_collected = True

    def remove_old_items(self):
        far_x = self.too_far_left_x()
        if self.items[0].x >= far_x:
            return
        self.items = [i for i in self.items if i.x >= far_x]

    # def hit_bullet(self):
    #     for i in self.bullets:
    #         if (not i.is_hit) and (i.hit_bul(self.player)):
    #             i.is_hit = True
    #
    # def remove_old_bullet(self):
    #     far_x = self.too_far_left_x()
    #     if self.bullets[0].x >= far_x:
    #         return
    #     self.bullets = [i for i in self.bullets if i.x >= far_x]

    def too_far_left_x(self):
        return self.player.x - self.width


    def recycle_building(self):
        far_x = self.too_far_left_x()
        for p in self.building:
            if p.right_most_x() < far_x:
                last_x = max([pp.right_most_x() for pp in self.building])
                p.x = last_x + randint(50, 200)
                p.y = randint(100, 200)
                self.items += p.spawn_items()

    def on_key_press(self, key, key_modifiers):
        if key == arcade.key.SPACE:
            self.player.jump()
            self.score += 1

    def start(self):
        self.state = World.STATE_STARTED
        t1 = time.time()
        return t1

    def freeze(self):
        # self.state = World.STATE_FROZEN
        t2 = time.time()
        return t2

    def is_started(self):
        return self.state == World.STATE_STARTED

    def die(self):
        self.state = World.STATE_DEAD