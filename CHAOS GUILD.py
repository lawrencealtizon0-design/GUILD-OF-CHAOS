"""
DUNGEON PARTY - a turn-based party RPG made with Python + Pygame.
All graphics are drawn in code (no image files needed).

Install:  pip install pygame
Run:      python dungeon_party.py

HOW TO PLAY
  * Your party of 3 heroes fights a group of undead. Every unit acts once per round,
    in the order shown in the TURN ORDER bar (top right). Speed decides the order.
  * On your hero's turn, 3 round skill buttons appear next to them.
    Click one (or press 1 / 2 / 3), then click a target.
  * Bottom-left buttons:  SWAP places (D = defend, P = potion also work)
        - Swap : trade formation slots with an ally (uses the turn)
        - Defend : take 50% less damage until your next turn, +4 MP
        - Potion : heal an ally for 40% max HP (shared stock)
  * ROWS: each side has 2 FRONT slots and 1 BACK slot. Melee attacks can only hit
    the front row while a front unit is alive. Ranged / magic skills hit anyone.
  * Skills cost MP, except the 3rd skill which is a SPECIAL that costs FOCUS
    (the yellow bar). Focus grows when you act and when you get hit.
  * Every floor has a different boss. Beat it, pick a perk, go deeper.
  * Right click / ESC cancels targeting.  ESC (no target) opens the pause menu.
    The >> button toggles fast battle speed.
"""
import math
import random
import sys

import pygame
from pygame import Vector2 as V

pygame.init()
W, H = 960, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Dungeon Party")
clock = pygame.time.Clock()


def font(size, bold=True):
    return pygame.font.SysFont("trebuchetms,verdana,dejavusans,arial", size, bold=bold)


F_XS, F_S, F_M, F_L, F_XL = font(13), font(16), font(20), font(30), font(54)

GOLD = (240, 200, 90)
WHITE = (240, 240, 245)
RED = (225, 70, 80)
BLUE = (70, 130, 240)
ORANGE = (240, 160, 40)
GREEN = (90, 220, 120)


def txt(surf, s, f, col, pos, anchor="topleft", shadow=True):
    img = f.render(str(s), True, col)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        surf.blit(f.render(str(s), True, (10, 8, 12)), r.move(1, 2))
    surf.blit(img, r)
    return r


def wrap(text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.size(t)[0] <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# =============================================================================
#  PIXEL-ART SPRITES (drawn procedurally on small canvases, then scaled up)
# =============================================================================
CW, CH = 42, 46
SKIN = (240, 190, 150)
BONE = (235, 230, 210)


def R(s, c, x, y, w, h):
    pygame.draw.rect(s, c, (x, y, w, h))


def C(s, c, x, y, r):
    pygame.draw.circle(s, c, (x, y), r)


def P(s, c, pts):
    pygame.draw.polygon(s, c, pts)


def spr_bard(s):
    R(s, (90, 60, 40), 12, 28, 3, 9); R(s, (90, 60, 40), 17, 28, 3, 9)
    R(s, (50, 35, 30), 11, 35, 5, 4); R(s, (50, 35, 30), 16, 35, 5, 4)
    R(s, (60, 110, 200), 10, 16, 12, 13); R(s, (40, 80, 160), 10, 16, 12, 2)
    R(s, (120, 80, 40), 10, 25, 12, 2)
    R(s, SKIN, 8, 17, 3, 8); R(s, SKIN, 21, 19, 5, 3)
    C(s, SKIN, 16, 10, 6)
    R(s, (245, 205, 80), 9, 3, 14, 5); R(s, (245, 205, 80), 9, 6, 3, 7)
    R(s, (245, 205, 80), 20, 6, 3, 6); R(s, (225, 175, 50), 12, 3, 6, 2)
    R(s, (30, 30, 50), 13, 10, 2, 2); R(s, (30, 30, 50), 18, 10, 2, 2)
    pygame.draw.ellipse(s, (170, 100, 45), (19, 22, 10, 10))
    pygame.draw.ellipse(s, (110, 60, 25), (19, 22, 10, 10), 1)
    C(s, (50, 25, 10), 24, 27, 2)
    pygame.draw.line(s, (120, 70, 30), (25, 24), (30, 11), 2)
    R(s, (80, 45, 20), 29, 8, 3, 4)


def spr_dwarf(s):
    R(s, (70, 55, 50), 10, 30, 5, 8); R(s, (70, 55, 50), 19, 30, 5, 8)
    R(s, (40, 35, 35), 9, 35, 7, 4); R(s, (40, 35, 35), 18, 35, 7, 4)
    R(s, (120, 125, 140), 7, 16, 20, 15); R(s, (155, 160, 175), 7, 16, 20, 3)
    R(s, (95, 60, 40), 7, 27, 20, 2); R(s, (240, 200, 70), 16, 27, 3, 2)
    R(s, (120, 125, 140), 3, 17, 5, 9); R(s, SKIN, 3, 25, 5, 3)
    R(s, (120, 125, 140), 27, 17, 5, 7); R(s, SKIN, 27, 24, 5, 3)
    C(s, SKIN, 17, 11, 6)
    R(s, (150, 155, 170), 10, 3, 14, 6); R(s, (110, 115, 130), 10, 7, 14, 2)
    R(s, (175, 180, 195), 15, 1, 4, 3)
    R(s, (30, 30, 40), 13, 12, 2, 2); R(s, (30, 30, 40), 20, 12, 2, 2)
    P(s, (215, 120, 40), [(10, 14), (24, 14), (23, 24), (17, 29), (11, 24)])
    R(s, (240, 150, 60), 12, 15, 10, 2)
    R(s, (100, 65, 35), 33, 8, 2, 26)
    R(s, (160, 165, 180), 29, 3, 10, 8); R(s, (205, 210, 225), 29, 3, 10, 2)


def spr_ranger(s):
    R(s, (85, 60, 40), 13, 29, 3, 9); R(s, (85, 60, 40), 19, 29, 3, 9)
    R(s, (45, 30, 25), 12, 35, 5, 4); R(s, (45, 30, 25), 18, 35, 5, 4)
    R(s, (50, 130, 70), 11, 17, 12, 13); R(s, (35, 100, 55), 11, 17, 12, 2)
    R(s, (110, 75, 40), 11, 26, 12, 2)
    P(s, (35, 95, 55), [(9, 16), (12, 16), (12, 32), (7, 34)])
    R(s, (120, 80, 45), 8, 13, 4, 10)
    R(s, (230, 230, 230), 9, 10, 1, 4); R(s, (230, 230, 230), 11, 10, 1, 4)
    R(s, SKIN, 10, 18, 3, 8); R(s, SKIN, 22, 19, 5, 3)
    C(s, (50, 135, 70), 17, 10, 7)
    R(s, SKIN, 13, 9, 8, 6)
    P(s, (50, 135, 70), [(10, 7), (5, 11), (11, 12)])
    R(s, (30, 30, 40), 14, 11, 2, 2); R(s, (30, 30, 40), 19, 11, 2, 2)
    pygame.draw.arc(s, (150, 100, 50), (22, 8, 14, 28), -math.pi / 2, math.pi / 2, 3)
    pygame.draw.line(s, (235, 235, 235), (29, 8), (29, 35), 1)


def spr_skeleton(s):
    R(s, BONE, 13, 28, 2, 10); R(s, BONE, 19, 28, 2, 10)
    R(s, BONE, 12, 37, 4, 2); R(s, BONE, 18, 37, 4, 2)
    R(s, (60, 55, 60), 12, 16, 10, 12)
    for y in (17, 20, 23, 26):
        R(s, BONE, 12, y, 10, 2)
    R(s, BONE, 16, 15, 2, 14); R(s, BONE, 11, 15, 12, 2); R(s, BONE, 13, 27, 8, 2)
    C(s, BONE, 17, 9, 6); R(s, BONE, 13, 12, 8, 4)
    R(s, (20, 15, 25), 13, 8, 3, 3); R(s, (20, 15, 25), 18, 8, 3, 3)
    R(s, (255, 90, 60), 14, 9, 1, 1); R(s, (255, 90, 60), 19, 9, 1, 1)
    R(s, (20, 15, 25), 16, 12, 2, 2)
    for x in (14, 16, 18, 20):
        R(s, (70, 65, 70), x, 15, 1, 2)
    R(s, BONE, 22, 16, 2, 9)
    R(s, (195, 200, 210), 26, 6, 3, 18); P(s, (195, 200, 210), [(26, 6), (29, 6), (27, 2)])
    R(s, (130, 85, 40), 24, 22, 7, 2); R(s, (130, 85, 40), 26, 24, 3, 4)
    C(s, (150, 95, 50), 9, 24, 7); C(s, (195, 55, 45), 9, 24, 5); C(s, (225, 205, 120), 9, 24, 2)


def spr_skelmage(s, robe=(70, 80, 120), trim=(190, 165, 90), orb=(90, 230, 255)):
    dark = tuple(max(0, c - 28) for c in robe)
    P(s, robe, [(10, 15), (24, 15), (29, 39), (5, 39)])
    R(s, trim, 5, 37, 24, 2)
    R(s, dark, 16, 15, 2, 23)
    P(s, dark, [(9, 14), (13, 12), (13, 20)]); P(s, dark, [(25, 14), (21, 12), (21, 20)])
    C(s, dark, 17, 9, 8)
    C(s, BONE, 17, 10, 5)
    R(s, (20, 15, 25), 13, 8, 3, 3); R(s, (20, 15, 25), 19, 8, 3, 3)
    R(s, orb, 14, 9, 1, 1); R(s, orb, 20, 9, 1, 1)
    P(s, (215, 215, 225), [(13, 14), (21, 14), (19, 22), (17, 25), (15, 22)])
    R(s, (110, 75, 40), 31, 6, 2, 33)
    C(s, orb, 32, 5, 4); C(s, (255, 255, 255), 32, 5, 1)
    R(s, BONE, 27, 20, 5, 2)


def spr_golem(s):
    stone, dark, light = (125, 125, 138), (80, 80, 94), (160, 160, 172)
    R(s, dark, 9, 30, 8, 9); R(s, dark, 22, 30, 8, 9)
    R(s, stone, 6, 12, 28, 19); R(s, light, 6, 12, 28, 3); R(s, dark, 6, 28, 28, 3)
    R(s, stone, 0, 14, 6, 18); R(s, light, 0, 14, 6, 3)
    R(s, stone, 34, 14, 6, 18); R(s, light, 34, 14, 6, 3)
    R(s, dark, 0, 30, 7, 6); R(s, dark, 33, 30, 7, 6)
    R(s, stone, 12, 3, 16, 10); R(s, light, 12, 3, 16, 2)
    R(s, (255, 150, 40), 15, 7, 4, 3); R(s, (255, 150, 40), 22, 7, 4, 3)
    R(s, (50, 50, 60), 17, 11, 6, 1)
    pygame.draw.line(s, (50, 50, 60), (12, 16), (17, 24), 1)
    pygame.draw.line(s, (50, 50, 60), (28, 18), (24, 27), 1)
    R(s, (75, 135, 75), 7, 12, 7, 2); R(s, (75, 135, 75), 26, 12, 6, 2); R(s, (75, 135, 75), 1, 14, 3, 2)
    pygame.draw.circle(s, (255, 150, 40), (20, 22), 4, 1); C(s, (255, 200, 90), 20, 22, 1)


def spr_lich(s):
    robe = (62, 40, 92)
    P(s, robe, [(10, 14), (30, 14), (36, 40), (4, 40)])
    R(s, (32, 20, 52), 19, 14, 2, 26)
    R(s, (205, 175, 60), 4, 38, 32, 2)
    P(s, (42, 30, 74), [(6, 13), (13, 9), (13, 19)]); P(s, (42, 30, 74), [(34, 13), (27, 9), (27, 19)])
    C(s, (30, 20, 50), 20, 10, 8)
    C(s, (235, 230, 215), 20, 10, 6); R(s, (235, 230, 215), 16, 13, 8, 4)
    R(s, (20, 15, 25), 16, 9, 3, 3); R(s, (20, 15, 25), 22, 9, 3, 3)
    R(s, (100, 210, 255), 17, 10, 1, 1); R(s, (100, 210, 255), 23, 10, 1, 1)
    P(s, (245, 205, 60), [(14, 5), (14, 1), (17, 3), (20, 0), (23, 3), (26, 1), (26, 5)])
    R(s, (75, 62, 85), 36, 6, 2, 35)
    C(s, (120, 255, 160), 37, 5, 4); C(s, (230, 255, 240), 37, 5, 1)
    R(s, (235, 230, 215), 31, 22, 6, 2)


SPRITES = {
    "bard": dict(fn=spr_bard, scale=3, feet=40, top=3, head=(8, 2, 18, 17)),
    "dwarf": dict(fn=spr_dwarf, scale=3, feet=40, top=1, head=(6, 0, 24, 25)),
    "ranger": dict(fn=spr_ranger, scale=3, feet=40, top=2, head=(5, 1, 20, 17)),
    "skeleton": dict(fn=spr_skeleton, scale=3, feet=40, top=2, head=(10, 2, 16, 16)),
    "skelmage": dict(fn=spr_skelmage, scale=3, feet=40, top=1, head=(7, 0, 20, 25)),
    "necro": dict(fn=lambda s: spr_skelmage(s, (95, 40, 115), (225, 185, 70), (255, 90, 200)),
                  scale=4, feet=40, top=1, head=(7, 0, 20, 25)),
    "golem": dict(fn=spr_golem, scale=4, feet=40, top=3, head=(9, 1, 22, 16)),
    "lich": dict(fn=spr_lich, scale=4, feet=41, top=0, head=(11, 0, 20, 18)),
}

_base, _img, _por = {}, {}, {}


def base_sprite(name):
    if name not in _base:
        s = pygame.Surface((CW, CH), pygame.SRCALPHA)
        SPRITES[name]["fn"](s)
        sil = pygame.mask.from_surface(s).to_surface(setcolor=(18, 12, 20, 255), unsetcolor=(0, 0, 0, 0))
        out = pygame.Surface((CW + 2, CH + 2), pygame.SRCALPHA)
        for dx in (0, 1, 2):
            for dy in (0, 1, 2):
                if (dx, dy) != (1, 1):
                    out.blit(sil, (dx, dy))
        out.blit(s, (1, 1))
        _base[name] = out
    return _base[name]


def sprite_img(name, flip=False, flash=False):
    key = (name, flip, flash)
    if key not in _img:
        b = base_sprite(name)
        if flash:
            b = pygame.mask.from_surface(b).to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        sc = SPRITES[name]["scale"]
        im = pygame.transform.scale(b, (b.get_width() * sc, b.get_height() * sc))
        _img[key] = pygame.transform.flip(im, True, False) if flip else im
    return _img[key]


def portrait(name, size, border):
    key = (name, size, border)
    if key not in _por:
        surf = pygame.Surface((size, size))
        surf.fill((36, 32, 42))
        pygame.draw.rect(surf, (54, 50, 64), (0, 0, size, size // 2))
        hx, hy, hw, hh = SPRITES[name]["head"]
        crop = base_sprite(name).subsurface((hx + 1, hy + 1, hw, hh)).copy()
        k = min((size - 6) / hw, (size - 6) / hh)
        crop = pygame.transform.scale(crop, (max(1, int(hw * k)), max(1, int(hh * k))))
        surf.blit(crop, crop.get_rect(center=(size // 2, size // 2)))
        pygame.draw.rect(surf, border, (0, 0, size, size), 3, border_radius=5)
        _por[key] = surf
    return _por[key]


# =============================================================================
#  ICONS
# =============================================================================
def draw_icon(s, kind, cx, cy, r, col=(235, 235, 245)):
    lw = max(2, int(r * 0.22))
    wood = (195, 135, 75)
    if kind == "hammer":
        pygame.draw.line(s, wood, (cx - r * .7, cy + r * .9), (cx + r * .3, cy - r * .2), lw + 1)
        P(s, col, [(cx - r * .1, cy - r * .95), (cx + r * .95, cy), (cx + r * .55, cy + r * .4), (cx - r * .55, cy - r * .55)])
    elif kind == "sword":
        pygame.draw.line(s, col, (cx - r * .7, cy + r * .7), (cx + r * .85, cy - r * .85), lw + 1)
        pygame.draw.line(s, wood, (cx - r * .7, cy), (cx, cy + r * .7), lw)
    elif kind == "shield":
        P(s, col, [(cx - r * .8, cy - r * .8), (cx + r * .8, cy - r * .8), (cx + r * .8, cy + r * .1), (cx, cy + r), (cx - r * .8, cy + r * .1)])
        P(s, (90, 110, 170), [(cx - r * .5, cy - r * .5), (cx + r * .5, cy - r * .5), (cx + r * .5, cy), (cx, cy + r * .6), (cx - r * .5, cy)])
    elif kind == "quake":
        pts = [(cx - r, cy - r * .2), (cx - r * .4, cy + r * .1), (cx - r * .2, cy - r * .5), (cx + r * .2, cy + r * .4), (cx + r * .5, cy - r * .2), (cx + r, cy + r * .1)]
        pygame.draw.lines(s, col, False, pts, lw)
        pygame.draw.line(s, wood, (cx - r, cy + r * .6), (cx + r, cy + r * .6), lw)
    elif kind == "arrow":
        pygame.draw.line(s, wood, (cx - r * .9, cy + r * .9), (cx + r * .6, cy - r * .6), lw)
        P(s, col, [(cx + r * .95, cy - r * .95), (cx + r * .2, cy - r * .6), (cx + r * .6, cy - r * .2)])
        pygame.draw.line(s, col, (cx - r * .9, cy + r * .9), (cx - r * .9, cy + r * .4), lw)
        pygame.draw.line(s, col, (cx - r * .9, cy + r * .9), (cx - r * .4, cy + r * .9), lw)
    elif kind == "drop":
        C(s, (110, 220, 120), cx, int(cy + r * .25), int(r * .65))
        P(s, (110, 220, 120), [(cx, cy - r), (cx - r * .6, cy), (cx + r * .6, cy)])
        C(s, (210, 255, 215), int(cx - r * .2), int(cy + r * .1), max(1, int(r * .15)))
    elif kind == "target":
        pygame.draw.circle(s, col, (cx, cy), int(r), lw)
        pygame.draw.circle(s, col, (cx, cy), int(r * .5), lw - 1 if lw > 2 else 1)
        pygame.draw.line(s, col, (cx - r * 1.1, cy), (cx + r * 1.1, cy), 2)
        pygame.draw.line(s, col, (cx, cy - r * 1.1), (cx, cy + r * 1.1), 2)
    elif kind == "note":
        pygame.draw.ellipse(s, col, (cx - r * .8, cy + r * .2, r * .9, r * .65))
        pygame.draw.line(s, col, (cx + r * .05, cy + r * .5), (cx + r * .05, cy - r * .9), lw)
        P(s, col, [(cx + r * .05, cy - r * .9), (cx + r * .8, cy - r * .5), (cx + r * .05, cy - r * .2)])
    elif kind == "heart":
        c2 = (240, 90, 120)
        C(s, c2, int(cx - r * .4), int(cy - r * .25), int(r * .5)); C(s, c2, int(cx + r * .4), int(cy - r * .25), int(r * .5))
        P(s, c2, [(cx - r * .88, cy - r * .1), (cx + r * .88, cy - r * .1), (cx, cy + r * .9)])
    elif kind == "swirl":
        pts = []
        for i in range(46):
            a = i * 0.42
            rad = r * (0.08 + 0.92 * i / 46)
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
        pygame.draw.lines(s, (150, 230, 235), False, pts, lw)
    elif kind == "bolt":
        P(s, (255, 230, 90), [(cx + r * .2, cy - r), (cx - r * .6, cy + r * .1), (cx - r * .05, cy + r * .1), (cx - r * .25, cy + r), (cx + r * .65, cy - r * .2), (cx + r * .05, cy - r * .2)])
    elif kind == "skull":
        C(s, col, cx, int(cy - r * .1), int(r * .75)); R(s, col, int(cx - r * .45), int(cy + r * .3), int(r * .9), int(r * .55))
        C(s, (25, 20, 30), int(cx - r * .3), int(cy - r * .1), max(2, int(r * .2))); C(s, (25, 20, 30), int(cx + r * .3), int(cy - r * .1), max(2, int(r * .2)))
    elif kind == "rock":
        P(s, (150, 150, 160), [(cx - r * .8, cy + r * .5), (cx - r * .6, cy - r * .5), (cx, cy - r * .9), (cx + r * .7, cy - r * .4), (cx + r * .9, cy + r * .4), (cx, cy + r * .8)])
        pygame.draw.line(s, (90, 90, 100), (cx - r * .2, cy - r * .5), (cx, cy + r * .2), 2)
    elif kind == "burst":
        pts = []
        for i in range(16):
            a = i * math.pi / 8
            rad = r if i % 2 == 0 else r * .45
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
        P(s, (200, 120, 255), pts)
    elif kind == "potion":
        R(s, (210, 210, 220), int(cx - r * .25), int(cy - r * .9), int(r * .5), int(r * .5))
        C(s, (225, 60, 90), cx, int(cy + r * .3), int(r * .7))
        C(s, (255, 170, 190), int(cx - r * .25), int(cy + r * .1), max(1, int(r * .15)))
    elif kind == "swap":
        g = (110, 230, 120)
        pygame.draw.line(s, g, (cx - r * .8, cy - r * .35), (cx + r * .5, cy - r * .35), lw)
        P(s, g, [(cx + r * .95, cy - r * .35), (cx + r * .35, cy - r * .85), (cx + r * .35, cy + r * .15)])
        pygame.draw.line(s, g, (cx + r * .8, cy + r * .45), (cx - r * .5, cy + r * .45), lw)
        P(s, g, [(cx - r * .95, cy + r * .45), (cx - r * .35, cy - r * .05), (cx - r * .35, cy + r * .95)])
    elif kind == "menu":
        for dy in (-.6, 0, .6):
            pygame.draw.line(s, col, (cx - r * .8, cy + r * dy), (cx + r * .8, cy + r * dy), lw)
    elif kind == "ff":
        P(s, col, [(cx - r * .9, cy - r * .7), (cx - r * .9, cy + r * .7), (cx, cy)])
        P(s, col, [(cx, cy - r * .7), (cx, cy + r * .7), (cx + r * .9, cy)])


def round_button(surf, center, r, icon, hover=False, disabled=False, badge=None, badge_col=BLUE, selected=False):
    x, y = center
    pygame.draw.circle(surf, (10, 8, 10), (x + 2, y + 4), r + 2)
    pygame.draw.circle(surf, (40, 38, 44), (x, y), r)
    pygame.draw.circle(surf, (66, 64, 72), (x, y - 2), r - 4)
    pygame.draw.circle(surf, (28, 26, 32), (x, y + 2), r - 6)
    ring = GOLD if (hover or selected) else (200, 204, 212)
    pygame.draw.circle(surf, ring, (x, y), r, 3)
    draw_icon(surf, icon, x, y, int(r * .52))
    if disabled:
        ov = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ov, (0, 0, 0, 150), (r, r), r)
        surf.blit(ov, (x - r, y - r))
    if badge is not None:
        bx, by = int(x + r * .72), int(y + r * .72)
        pygame.draw.circle(surf, (15, 12, 16), (bx, by), 11)
        pygame.draw.circle(surf, badge_col, (bx, by), 10)
        txt(surf, badge, F_XS, WHITE, (bx, by), "center", shadow=False)


# =============================================================================
#  BACKGROUND, LIGHTING
# =============================================================================
def make_background():
    rnd = random.Random(7)
    bg = pygame.Surface((W, H))
    wall_h = 245
    bg.fill((24, 26, 36))
    by, row = 0, 0
    while by < wall_h:
        bx = -36 if row % 2 else 0
        while bx < W:
            sh = rnd.randint(-6, 8)
            pygame.draw.rect(bg, (44 + sh, 48 + sh, 62 + sh), (bx + 2, by + 2, 70, 31), border_radius=3)
            bx += 72
        by += 34
        row += 1
    pygame.draw.rect(bg, (9, 10, 15), (250, 76, 190, wall_h - 76))
    pygame.draw.ellipse(bg, (9, 10, 15), (250, 32, 190, 90))
    for px in (230, 440):
        pygame.draw.rect(bg, (72, 78, 96), (px, 62, 22, wall_h - 62))
        pygame.draw.rect(bg, (38, 42, 56), (px, 62, 22, wall_h - 62), 3)
    pygame.draw.arc(bg, (72, 78, 96), (240, 26, 210, 104), 0, math.pi, 12)
    pygame.draw.rect(bg, (90, 98, 114), (0, wall_h - 6, W, 12))
    pygame.draw.rect(bg, (36, 40, 52), (0, wall_h + 6, W, 8))
    pygame.draw.rect(bg, (38, 44, 56), (0, wall_h + 12, W, H))
    y = wall_h + 12
    while y < H:
        rh = int(46 + (y - wall_h) * 0.12)
        x = -rnd.randint(0, 80)
        while x < W:
            rw = rnd.randint(int(rh * 1.3), int(rh * 2.6))
            sh = rnd.randint(-10, 10)
            pygame.draw.rect(bg, (88 + sh, 100 + sh, 117 + sh), (x + 2, y + 2, rw - 4, rh - 4), border_radius=10)
            pygame.draw.rect(bg, (112 + sh, 126 + sh, 142 + sh), (x + 8, y + 4, rw - 16, 4), border_radius=3)
            x += rw
        y += rh
    rune = (122, 144, 168)
    pygame.draw.ellipse(bg, rune, (540, 300, 420, 240), 5)
    pygame.draw.ellipse(bg, rune, (590, 330, 320, 180), 3)
    for i in range(12):
        a = i * math.tau / 12
        p1 = (750 + math.cos(a) * 210, 420 + math.sin(a) * 120)
        p2 = (750 + math.cos(a) * 160, 420 + math.sin(a) * 90)
        pygame.draw.line(bg, rune, p1, p2, 3)
    return bg


def make_vignette():
    small = pygame.Surface((96, 72), pygame.SRCALPHA)
    for x in range(96):
        for y in range(72):
            d = math.hypot((x - 48) / 48, (y - 36) / 36)
            small.set_at((x, y), (0, 0, 0, max(0, min(255, int((d - 0.55) * 330)))))
    return pygame.transform.smoothscale(small, (W, H))


def make_glow(size, col):
    g = pygame.Surface((size, size), pygame.SRCALPHA)
    for x in range(size):
        for y in range(size):
            d = math.hypot(x - size / 2, y - size / 2) / (size / 2)
            if d < 1:
                g.set_at((x, y), (*col, int(90 * (1 - d) ** 2)))
    return g


BACKGROUND = make_background()
VIGNETTE = make_vignette()
TORCH_GLOW = make_glow(260, (255, 170, 70))
HERO_SLOTS = [V(345, 345), V(325, 480), V(150, 410)]
FOE_SLOTS = [V(625, 345), V(645, 480), V(815, 410)]


def slot_pos(team, slot):
    return (HERO_SLOTS if team == "hero" else FOE_SLOTS)[slot].copy()


def draw_torch(surf, t):
    tx, ty = 468, 112
    surf.blit(TORCH_GLOW, (tx - 130, ty - 150), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surf, (30, 26, 28), (tx - 4, ty, 8, 22))
    pygame.draw.polygon(surf, (50, 44, 48), [(tx - 12, ty), (tx + 12, ty), (tx + 7, ty + 12), (tx - 7, ty + 12)])
    f = math.sin(t * 11) * 3 + math.sin(t * 7.3) * 2
    pygame.draw.polygon(surf, (240, 110, 30), [(tx - 9, ty), (tx - 4 + f * .3, ty - 22), (tx + f, ty - 34 - f), (tx + 5 + f * .3, ty - 20), (tx + 9, ty)])
    pygame.draw.polygon(surf, (255, 200, 80), [(tx - 5, ty), (tx + f * .2, ty - 22), (tx + 5, ty)])


# =============================================================================
#  GAME DATA
# =============================================================================
class Skill:
    def __init__(self, name, icon, desc, target="enemy", power=0.0, mp=0, focus=0, melee=False,
                 heal=0.0, effects=None, ignore_def=False, cooldown=0, ai=None, weight=1,
                 color=(255, 255, 255), proj=None, drain=0.0, special=None):
        for k, v in list(locals().items()):
            if k != "self":
                setattr(self, k, v)
        self.effects = effects or {}


TARGET_TEXT = {"enemy": "One enemy", "enemies": "All enemies", "ally": "One ally", "allies": "All allies",
               "self": "Self", "ally_other": "Another ally", "dead_ally": "A fallen ally"}

# ----- hero skills
S_SOUR = Skill("Sour Note", "note", "A jarring chord that hurts one enemy. Ranged.", power=1.0, proj="note", color=(255, 230, 120))
S_HEAL = Skill("Healing Song", "heart", "Restore 22 HP to one ally.", target="ally", heal=22, mp=8, color=(120, 255, 150))
S_HYMN = Skill("Battle Hymn", "swirl", "SPECIAL: the whole party gains +30% attack for 3 turns.", target="allies", effects={"atk_up": 3}, focus=50, color=(150, 230, 235))
S_HAMMER = Skill("Hammer Blow", "hammer", "A crushing strike. Melee: hits the front row only.", power=1.1, melee=True, color=(255, 210, 140))
S_BASH = Skill("Shield Bash", "shield", "Melee hit with a 70% chance to stun the target.", power=0.8, mp=6, melee=True, effects={"stun": (1, 0.7)}, color=(180, 200, 255))
S_QUAKE = Skill("Earthquake", "quake", "SPECIAL: shake the ground, hurting ALL enemies.", target="enemies", power=0.9, focus=50, color=(200, 170, 120))
S_SHOT = Skill("Quick Shot", "arrow", "A swift arrow. Ranged: can hit any row.", power=1.0, proj="arrow", color=(255, 240, 200))
S_POISON = Skill("Poison Arrow", "drop", "Poisons the target: 4 damage per turn for 3 turns.", power=0.6, mp=6, proj="arrow", effects={"poison": (3, 4)}, color=(120, 230, 120))
S_DEADEYE = Skill("Deadeye", "target", "SPECIAL: a huge shot that ignores armor.", power=2.3, focus=50, proj="arrow", ignore_def=True, color=(255, 120, 90))

# ----- enemy skills
S_SLASH = Skill("Slash", "sword", "", power=1.0, melee=True, weight=3, color=(220, 220, 230))
S_RAISE = Skill("Raise Shield", "shield", "", target="self", effects={"def_up": 3}, cooldown=4, ai="buff_self", color=(170, 190, 255))
S_BONE = Skill("Bone Bolt", "bolt", "", power=1.0, proj="bolt", weight=3, color=(160, 255, 220))
S_MEND = Skill("Mend Bones", "heart", "", target="ally", heal=16, ai="heal", color=(120, 255, 150))
S_HEX = Skill("Hex", "skull", "", power=0.4, proj="bolt", effects={"atk_down": 3}, cooldown=3, weight=2, color=(230, 100, 230))
S_SLAM = Skill("Slam", "hammer", "", power=1.2, melee=True, weight=3, effects={"stun": (1, 0.35)}, color=(230, 200, 150))
S_HARDEN = Skill("Harden", "shield", "", target="self", effects={"def_up": 3}, cooldown=4, ai="buff_self", color=(190, 190, 210))
S_ROCK = Skill("Boulder Toss", "rock", "", power=0.9, proj="orb", weight=2, color=(170, 170, 180))
S_DRAIN = Skill("Soul Drain", "skull", "", power=1.0, proj="bolt", drain=0.6, weight=3, color=(120, 255, 170))
S_NOVA = Skill("Death Nova", "burst", "", target="enemies", power=0.55, cooldown=3, weight=3, color=(200, 120, 255))
S_RAISEDEAD = Skill("Raise Dead", "swirl", "", target="dead_ally", heal=0.45, cooldown=4, ai="revive", color=(120, 255, 160))

SPECIALS = {
    "defend": Skill("Defend", "shield", "Brace: take 50% less damage until your next turn. Restores 4 MP.", target="self", special="defend"),
    "potion": Skill("Healing Potion", "potion", "Heal an ally for 40% of their max HP. Shared stock.", target="ally", special="potion"),
    "swap": Skill("Swap Places", "swap", "Trade formation slots with an ally (uses your turn). The front row takes melee hits.", target="ally_other", special="swap"),
}

HEROES = [
    dict(name="Brom", sprite="dwarf", hp=70, mp=18, atk=11, df=3, spd=4, slot=0, skills=[S_HAMMER, S_BASH, S_QUAKE]),
    dict(name="Lyra", sprite="ranger", hp=52, mp=22, atk=10, df=1, spd=9, slot=1, skills=[S_SHOT, S_POISON, S_DEADEYE]),
    dict(name="Pod", sprite="bard", hp=44, mp=30, atk=8, df=1, spd=7, slot=2, skills=[S_SOUR, S_HEAL, S_HYMN]),
]
FOE_T = {
    "skeleton": dict(name="Skeleton", sprite="skeleton", hp=38, mp=99, atk=8, df=2, spd=5, skills=[S_SLASH, S_RAISE]),
    "skelmage": dict(name="Bone Mage", sprite="skelmage", hp=30, mp=99, atk=8, df=0, spd=6, skills=[S_BONE, S_MEND]),
    "necro": dict(name="Mordo", sprite="necro", hp=95, mp=99, atk=9, df=1, spd=6, boss=True, skills=[S_BONE, S_HEX, S_MEND]),
    "golem": dict(name="Grumlock", sprite="golem", hp=150, mp=99, atk=11, df=4, spd=3, boss=True, skills=[S_SLAM, S_HARDEN, S_ROCK]),
    "lich": dict(name="Vexar", sprite="lich", hp=190, mp=99, atk=11, df=2, spd=7, boss=True, skills=[S_DRAIN, S_NOVA, S_RAISEDEAD]),
}
FLOORS = [
    dict(name="The Forgotten Crypt", boss="Mordo the Necromancer", enemies=[("skeleton", 0), ("skeleton", 1), ("necro", 2)]),
    dict(name="The Sunken Vault", boss="Grumlock the Stone Golem", enemies=[("golem", 0), ("skeleton", 1), ("skelmage", 2)]),
    dict(name="The Throne of Bone", boss="Vexar the Lich King", enemies=[("skeleton", 0), ("skeleton", 1), ("lich", 2)]),
]


def perk_hp(g):
    for h in g.heroes:
        h.max_hp += 8
        h.hp += 8


def perk_atk(g):
    for h in g.heroes:
        h.atk += 2


def perk_mp(g):
    for h in g.heroes:
        h.max_mp += 6
        h.mp += 6


def perk_spd(g):
    for h in g.heroes:
        h.spd += 1


def perk_pot(g):
    g.potions += 2


def perk_def(g):
    for h in g.heroes:
        h.df += 1


PERKS = [("Iron Will", "+8 max HP for everyone", perk_hp), ("Sharpened Steel", "+2 attack for everyone", perk_atk),
         ("Arcane Flow", "+6 max MP for everyone", perk_mp), ("Quick Feet", "+1 speed for everyone", perk_spd),
         ("Medic's Pack", "+2 healing potions", perk_pot), ("Thick Skin", "+1 defense for everyone", perk_def)]


# =============================================================================
#  UNITS / EFFECTS
# =============================================================================
class Unit:
    def __init__(self, t, team, slot, scale=1.0):
        self.name, self.sprite, self.team, self.slot = t["name"], t["sprite"], team, slot
        self.max_hp = int(t["hp"] * scale)
        self.hp = self.max_hp
        self.max_mp = t.get("mp", 0)
        self.mp = self.max_mp
        self.atk = round(t["atk"] * (1 + (scale - 1) * 0.6))
        self.df, self.spd = t["df"], t["spd"]
        self.skills = t["skills"]
        self.boss = t.get("boss", False)
        self.focus = 30 if team == "hero" else 0
        self.pos = slot_pos(team, slot)
        self.alive = True
        self.fade = 1.0
        self.reset_state()

    def reset_state(self):
        self.status, self.cd = {}, {}
        self.guard = False
        self.off = V(0, 0)
        self.anim = None
        self.flash = self.shake = 0.0
        self.t = random.random() * 6

    def rect(self):
        sp = SPRITES[self.sprite]
        sc = sp["scale"]
        w, h = 30 * sc * 0.8, (sp["feet"] - sp["top"]) * sc
        return pygame.Rect(self.pos.x + self.off.x - w / 2, self.pos.y - h, w, h)

    def center(self):
        r = self.rect()
        return V(r.centerx, r.centery)

    def top_y(self):
        sp = SPRITES[self.sprite]
        return self.pos.y + self.off.y - (sp["feet"] - sp["top"]) * sp["scale"]

    def update(self, dt):
        self.t += dt
        self.pos += (slot_pos(self.team, self.slot) - self.pos) * min(1.0, 7 * dt)
        self.flash = max(0, self.flash - dt)
        self.shake = max(0, self.shake - dt)
        if self.anim:
            a = self.anim
            a["t"] += dt
            self.off = a["vec"] * math.sin(math.pi * min(1, a["t"] / a["dur"]))
            if a["t"] >= a["dur"]:
                self.anim, self.off = None, V(0, 0)
        if not self.alive and self.fade > 0:
            self.fade = max(0, self.fade - dt * 1.6)

    def draw(self, surf):
        if not self.alive and self.fade <= 0:
            return
        sp = SPRITES[self.sprite]
        flash = self.flash > 0 and int(self.flash * 30) % 2 == 0
        img = sprite_img(self.sprite, flip=(self.team == "foe"), flash=flash)
        bob = math.sin(self.t * 2.6) * 2 if self.alive else (1 - self.fade) * 14
        sx = math.sin(self.t * 90) * 4 if self.shake > 0 else 0
        x = self.pos.x + self.off.x + sx
        y = self.pos.y + self.off.y + bob
        sh = pygame.Surface((90, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 90, 24))
        surf.blit(sh, (self.pos.x - 45, self.pos.y - 14))
        if self.fade < 1:
            img = img.copy()
            img.set_alpha(int(255 * self.fade))
        surf.blit(img, (x - img.get_width() / 2, y - sp["feet"] * sp["scale"]))


class Proj:
    def __init__(self, a, b, kind, col, dur):
        self.a, self.b, self.kind, self.col, self.dur, self.t = V(a), V(b), kind, col, dur, 0.0

    @property
    def pos(self):
        return self.a.lerp(self.b, min(1, self.t / self.dur))

    def draw(self, s):
        p = self.pos
        d = safe_dir(self.b - self.a)
        if self.kind == "arrow":
            pygame.draw.line(s, (200, 150, 90), p - d * 26, p, 3)
            P(s, (230, 230, 240), [p + d * 8, p - d * 2 + V(-d.y, d.x) * 5, p - d * 2 - V(-d.y, d.x) * 5])
        elif self.kind == "note":
            pygame.draw.ellipse(s, self.col, (p.x - 7, p.y - 4, 12, 9))
            pygame.draw.line(s, self.col, (p.x + 4, p.y), (p.x + 4, p.y - 18), 3)
            pygame.draw.line(s, self.col, (p.x + 4, p.y - 18), (p.x + 12, p.y - 12), 3)
        elif self.kind == "orb":
            C(s, (110, 110, 120), int(p.x), int(p.y), 12)
            C(s, (160, 160, 172), int(p.x - 3), int(p.y - 3), 6)
        else:
            C(s, self.col, int(p.x), int(p.y), 11)
            C(s, (255, 255, 255), int(p.x), int(p.y), 5)
            for i in range(1, 4):
                C(s, self.col, int(p.x - d.x * i * 9), int(p.y - d.y * i * 9), 9 - i * 2)


def safe_dir(v):
    return v.normalize() if v.length() > 0.01 else V(1, 0)


# =============================================================================
#  THE GAME
# =============================================================================
class Game:
    def __init__(self):
        self.t = 0.0
        self.paused = False
        self.fast = False
        self.new_run()
        self.state = "title"

    # ------------------------------------------------------------------ setup
    def new_run(self):
        self.floor = 0
        self.potions = 3
        self.heroes = [Unit(t, "hero", t["slot"]) for t in HEROES]
        self.start_floor()

    def start_floor(self):
        fl = FLOORS[self.floor]
        scale = 1 + 0.2 * self.floor
        foes = []
        for key, slot in fl["enemies"]:
            t = FOE_T[key]
            foes.append(Unit(t, "foe", slot, 1.0 if t.get("boss") else scale))
        self.units = self.heroes + foes
        for h in self.heroes:
            h.reset_state()
            h.fade = 1.0 if h.alive else 0
            h.pos = slot_pos("hero", h.slot) - V(380, 0)
        for f in foes:
            f.pos += V(380, 0)
        self.queue, self.current, self.round = [], None, 0
        self.texts, self.parts, self.projs = [], [], []
        self.pending, self.script, self.after = None, None, None
        self.shake, self.banner, self.banner_t = 0.0, "", 0.0
        self.intro_t = 2.6
        self.phase, self.timer, self.after = "wait", 2.6, self.next_turn
        self.tip = None
        self.state = "battle"

    # ---------------------------------------------------------------- helpers
    def living(self, team):
        return [u for u in self.units if u.team == team and u.alive]

    def enemies_of(self, u):
        return self.living("foe" if u.team == "hero" else "hero")

    def say(self, s, dur=1.8):
        self.banner, self.banner_t = s, dur

    def popup(self, pos, s, col, size=22):
        self.texts.append(dict(s=s, p=V(pos), col=col, t=0.0, size=size))

    def burst(self, pos, col, n=14, spd=160):
        for _ in range(n):
            a = random.random() * math.tau
            v = random.uniform(.3, 1) * spd
            self.parts.append([pos[0], pos[1], math.cos(a) * v, math.sin(a) * v - 40, 0.0, random.uniform(.35, .7), col, random.randint(3, 6)])

    def order(self):
        return sorted(self.living("hero") + self.living("foe"), key=lambda u: (-u.spd, u.team != "hero", self.units.index(u)))

    def upcoming(self, n=8):
        res = [self.current] if self.current and self.current.alive else []
        res += [u for u in self.queue if u.alive]
        o = self.order()
        while o and len(res) < n:
            res += o
        return res[:n]

    def usable(self, u, s):
        return u.mp >= s.mp and u.focus >= s.focus and u.cd.get(s.name, 0) <= 0

    def valid_targets(self, user, s):
        mine = self.living(user.team)
        opp = self.enemies_of(user)
        if s.target == "enemy":
            if s.melee:
                front = [u for u in opp if u.slot < 2]
                if front:
                    return front
            return opp
        if s.target == "ally":
            return mine
        if s.target == "ally_other":
            return [u for u in mine if u is not user]
        if s.target == "dead_ally":
            return [u for u in self.units if u.team == user.team and not u.alive and not u.boss]
        return []

    # --------------------------------------------------------------- turn flow
    def check_end(self):
        if not self.living("foe"):
            self.phase, self.timer, self.after = "victory", 1.8, self.on_victory
            self.say("VICTORY!", 3)
            return True
        if not self.living("hero"):
            self.phase, self.timer, self.after = "victory", 1.8, self.on_defeat
            self.say("Your party has fallen...", 3)
            return True
        return False

    def next_turn(self):
        if self.check_end():
            return
        while True:
            if not self.queue:
                self.queue = self.order()
                self.round += 1
            u = self.queue.pop(0)
            if u.alive:
                break
        self.current = u
        self.start_turn(u)

    def start_turn(self, u):
        u.guard = False
        for k in ("atk_up", "atk_down", "def_up"):
            if k in u.status:
                u.status[k] -= 1
                if u.status[k] <= 0:
                    del u.status[k]
        for k in list(u.cd):
            u.cd[k] = max(0, u.cd[k] - 1)
        if "poison" in u.status:
            turns, dmg = u.status["poison"]
            self.damage_unit(u, dmg, (120, 230, 120), source_text="")
            if turns - 1 <= 0:
                del u.status["poison"]
            else:
                u.status["poison"] = (turns - 1, dmg)
            if not u.alive:
                self.phase, self.timer, self.after = "wait", 0.9, self.next_turn
                return
        if "stun" in u.status:
            del u.status["stun"]
            self.popup(u.center() + V(0, -60), "Stunned!", (255, 230, 90))
            self.phase, self.timer, self.after = "wait", 1.0, self.next_turn
            return
        if u.team == "hero":
            self.phase = "choose"
        else:
            self.phase, self.timer = "foe_think", 0.8

    def on_victory(self):
        if self.floor >= len(FLOORS) - 1:
            self.state = "win"
        else:
            self.perks = random.sample(PERKS, 3)
            self.state = "reward"

    def on_defeat(self):
        self.state = "gameover"

    def finish_action(self):
        self.script, self.pending = None, None
        self.phase, self.timer, self.after = "wait", 0.35, self.next_turn

    # ---------------------------------------------------------------- combat
    def calc(self, user, tgt, s):
        atk = user.atk * (1.3 if "atk_up" in user.status else 1) * (0.7 if "atk_down" in user.status else 1)
        df = 0 if s.ignore_def else tgt.df * (1.6 if "def_up" in tgt.status else 1)
        dmg = max(1, round(atk * s.power * random.uniform(.9, 1.1) - df))
        crit = random.random() < 0.1
        if crit:
            dmg = round(dmg * 1.5)
        if tgt.guard:
            dmg = max(1, dmg // 2)
        return dmg, crit

    def damage_unit(self, u, dmg, col=RED, crit=False, source_text=None):
        u.hp -= dmg
        u.flash = 0.25
        u.shake = 0.2
        self.shake = max(self.shake, 0.18 if not crit else 0.3)
        self.popup(u.center() + V(random.randint(-10, 10), -50), ("CRIT " if crit else "") + str(dmg), (255, 220, 60) if crit else col, 30 if crit else 24)
        self.burst(u.center(), col, 8, 120)
        if u.team == "hero":
            u.focus = min(100, u.focus + 12)
        if u.hp <= 0:
            u.hp = 0
            u.alive = False
            u.fade = 1.0
            u.status = {}
            self.burst(u.center(), (230, 230, 240), 26, 220)

    def heal_unit(self, u, amt):
        amt = min(amt, u.max_hp - u.hp)
        u.hp += amt
        self.popup(u.center() + V(0, -50), f"+{amt}", GREEN, 24)
        self.burst(u.center(), (120, 255, 150), 12, 90)

    def apply_effects(self, s, tgt):
        for k, v in s.effects.items():
            if k == "stun":
                turns, prob = v
                if random.random() < prob:
                    tgt.status["stun"] = turns
                    self.popup(tgt.center() + V(0, -80), "Stunned!", (255, 230, 90), 20)
            elif k == "poison":
                tgt.status["poison"] = v
                self.popup(tgt.center() + V(0, -80), "Poisoned", (120, 230, 120), 20)
            else:
                tgt.status[k] = v + 1
                label = {"atk_up": "Attack up", "atk_down": "Attack down", "def_up": "Defense up"}[k]
                self.popup(tgt.center() + V(0, -80), label, (150, 230, 255) if k != "atk_down" else (230, 120, 230), 20)

    def hit(self, user, tgt, s):
        dmg, crit = self.calc(user, tgt, s)
        self.damage_unit(tgt, dmg, crit=crit)
        self.burst(tgt.center(), s.color, 10, 180)
        if s.drain:
            self.heal_unit(user, int(dmg * s.drain))
        if tgt.alive and s.effects:
            self.apply_effects(s, tgt)

    def action_gen(self, user, s, targets):
        sp = s.special
        if sp is None:
            user.mp -= s.mp
            user.focus = max(0, user.focus - s.focus)
            if s.cooldown:
                user.cd[s.name] = s.cooldown
            self.say(f"{user.name} uses {s.name}!")
        yield 0.3
        if sp == "defend":
            user.guard = True
            user.mp = min(user.max_mp, user.mp + 4)
            user.focus = min(100, user.focus + 15)
            self.popup(user.center() + V(0, -60), "Guarding", (150, 190, 255))
            self.burst(user.center(), (150, 190, 255), 16, 100)
            self.say(f"{user.name} defends.")
            yield 0.8
        elif sp == "potion":
            self.potions -= 1
            self.say(f"{user.name} uses a potion on {targets[0].name}.")
            user.anim = dict(t=0, dur=0.35, vec=V(0, -14))
            yield 0.3
            self.heal_unit(targets[0], int(targets[0].max_hp * 0.4))
            yield 0.7
        elif sp == "swap":
            a, b = user, targets[0]
            a.slot, b.slot = b.slot, a.slot
            self.say(f"{a.name} and {b.name} swap places.")
            yield 0.8
        elif s.target == "dead_ally":
            t = targets[0]
            user.anim = dict(t=0, dur=0.4, vec=V(0, -16))
            yield 0.35
            t.alive, t.fade, t.hp = True, 1.0, int(t.max_hp * s.heal)
            t.status = {}
            self.burst(t.center(), (120, 255, 160), 30, 200)
            self.popup(t.center() + V(0, -60), "Risen!", (120, 255, 160))
            yield 0.8
        elif s.power > 0:
            first = targets[0]
            if s.melee and len(targets) == 1:
                user.anim = dict(t=0, dur=0.45, vec=(first.pos - user.pos) * 0.78)
                yield 0.22
            elif s.proj:
                user.anim = dict(t=0, dur=0.3, vec=V(-8 if user.team == "hero" else 8, -8))
                yield 0.18
                dist = max(t.center().distance_to(user.center()) for t in targets)
                dur = max(0.25, dist / 900)
                for t in targets:
                    self.projs.append(Proj(user.center(), t.center(), s.proj, s.color, dur))
                yield dur
            else:
                user.anim = dict(t=0, dur=0.4, vec=V(0, -16))
                yield 0.25
                for t in targets:
                    self.burst(t.center(), s.color, 20, 220)
            for t in targets:
                self.hit(user, t, s)
            yield 0.7
        else:
            user.anim = dict(t=0, dur=0.4, vec=V(0, -16))
            yield 0.25
            for t in targets:
                if s.heal:
                    self.heal_unit(t, int(s.heal + user.atk * 0.3))
                if s.effects:
                    self.apply_effects(s, t)
                    self.burst(t.center(), s.color, 14, 110)
            yield 0.7
        if sp is None and s.focus == 0:
            user.focus = min(100, user.focus + 20)

    def start_action(self, user, s, targets):
        self.phase = "exec"
        self.pending = None
        self.script = self.action_gen(user, s, targets)
        self.timer = 0.0

    # ---------------------------------------------------------------- foe AI
    def foe_act(self, u):
        mine = self.living(u.team)
        cands = []
        for s in u.skills:
            if not self.usable(u, s):
                continue
            w = s.weight
            if s.ai == "heal":
                if not any(a.hp < a.max_hp * 0.6 for a in mine):
                    continue
                w = 5
            elif s.ai == "revive":
                if not self.valid_targets(u, s):
                    continue
                w = 8
            elif s.ai == "buff_self":
                if any(k in u.status for k in s.effects):
                    continue
                w = 2
            cands.append((s, w))
        if not cands:
            cands = [(u.skills[0], 1)]
        s = random.choices([c[0] for c in cands], [c[1] for c in cands])[0]
        if s.target == "enemy":
            vt = self.valid_targets(u, s)
            t = random.choices(vt, [2.5 - t.hp / t.max_hp for t in vt])[0]
            targets = [t]
        elif s.target == "ally":
            targets = [min(mine, key=lambda a: a.hp / a.max_hp)]
        elif s.target == "enemies":
            targets = self.enemies_of(u)
        elif s.target == "allies":
            targets = mine
        elif s.target == "dead_ally":
            targets = [random.choice(self.valid_targets(u, s))]
        else:
            targets = [u]
        self.start_action(u, s, targets)

    # ------------------------------------------------------------ hero input
    def hero_turn(self):
        return self.state == "battle" and self.phase in ("choose", "target") and self.current and self.current.team == "hero"

    def pick_skill(self, s):
        u = self.current
        if s.special == "potion" and self.potions <= 0:
            self.say("No potions left!", 1.2)
            return
        if not self.usable(u, s):
            self.say("Not enough MP / Focus!", 1.2)
            return
        if s.target in ("enemies", "allies", "self"):
            tg = {"enemies": self.living("foe"), "allies": self.living("hero"), "self": [u]}[s.target]
            self.start_action(u, s, tg)
        else:
            if not self.valid_targets(u, s):
                self.say("No valid target.", 1.2)
                return
            self.pending = s
            self.phase = "target"

    def confirm_target(self, tgt):
        if self.phase == "target" and self.pending and tgt in self.valid_targets(self.current, self.pending):
            self.start_action(self.current, self.pending, [tgt])

    def radial_centers(self, u):
        c = V(u.pos.x, u.pos.y - 60)
        return [c + V(92, -84), c + V(134, 0), c + V(92, 84)]

    BOTTOM = {"swap": (48, 672), "defend": (112, 672), "potion": (176, 672)}

    def click(self, pos, button=1):
        pos = V(pos)
        if self.paused:
            for name, r in self.menu_rects.items():
                if r.collidepoint(pos):
                    if name == "resume":
                        self.paused = False
                    elif name == "restart":
                        self.new_run()
                        self.paused = False
                    elif name == "quit":
                        pygame.quit()
                        sys.exit()
            return
        if self.state == "title":
            self.new_run()
            return
        if self.state in ("gameover", "win"):
            self.new_run()
            self.state = "title"
            return
        if self.state == "reward":
            for i, r in enumerate(self.perk_rects()):
                if r.collidepoint(pos):
                    self.perks[i][2](self)
                    for h in self.heroes:
                        if not h.alive:
                            h.alive, h.hp = True, int(h.max_hp * 0.35)
                        else:
                            h.hp = min(h.max_hp, h.hp + int(h.max_hp * 0.35))
                        h.mp = min(h.max_mp, h.mp + h.max_mp // 2)
                        h.focus = max(h.focus, 30)
                    self.floor += 1
                    self.start_floor()
            return
        # battle
        if pygame.Rect(W - 114, H - 54, 40, 40).collidepoint(pos):
            self.paused = True
            return
        if pygame.Rect(W - 64, H - 54, 40, 40).collidepoint(pos):
            self.fast = not self.fast
            return
        if not self.hero_turn():
            return
        if button == 3:
            self.pending, self.phase = None, "choose"
            return
        u = self.current
        for s, c in zip(u.skills, self.radial_centers(u)):
            if (pos - c).length() <= 28:
                self.pending, self.phase = None, "choose"
                self.pick_skill(s)
                return
        for name, c in self.BOTTOM.items():
            if (pos - V(c)).length() <= 28:
                self.pending, self.phase = None, "choose"
                self.pick_skill(SPECIALS[name])
                return
        if self.phase == "target":
            for t in self.units:
                if t.alive and t.rect().collidepoint(pos):
                    self.confirm_target(t)
                    return
            self.pending, self.phase = None, "choose"

    def key(self, k):
        if k == pygame.K_ESCAPE:
            if self.state == "title":
                pygame.quit()
                sys.exit()
            if self.paused:
                self.paused = False
            elif self.phase == "target":
                self.pending, self.phase = None, "choose"
            elif self.state == "battle":
                self.paused = True
            return
        if self.state in ("title", "gameover", "win") and k in (pygame.K_RETURN, pygame.K_SPACE):
            self.click((0, 0))
            return
        if self.paused or not self.hero_turn():
            return
        u = self.current
        idx = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}.get(k)
        if idx is not None:
            self.pending, self.phase = None, "choose"
            self.pick_skill(u.skills[idx])
        elif k == pygame.K_d:
            self.pending, self.phase = None, "choose"
            self.pick_skill(SPECIALS["defend"])
        elif k == pygame.K_p:
            self.pending, self.phase = None, "choose"
            self.pick_skill(SPECIALS["potion"])
        elif k == pygame.K_s:
            self.pending, self.phase = None, "choose"
            self.pick_skill(SPECIALS["swap"])

    # ---------------------------------------------------------------- update
    def update(self, dt):
        self.t += dt
        for u in self.units:
            u.update(dt)
        if self.state != "battle" or self.paused:
            return
        if self.fast:
            dt *= 2
        self.shake = max(0, self.shake - dt)
        self.banner_t = max(0, self.banner_t - dt)
        self.intro_t = max(0, self.intro_t - dt)
        for p in self.projs:
            p.t += dt
        self.projs = [p for p in self.projs if p.t < p.dur]
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 380 * dt
            p[4] += dt
        self.parts = [p for p in self.parts if p[4] < p[5]]
        for tx in self.texts:
            tx["t"] += dt
            tx["p"].y -= 38 * dt
        self.texts = [tx for tx in self.texts if tx["t"] < 1.3]

        if self.phase in ("wait", "victory"):
            self.timer -= dt
            if self.timer <= 0 and self.after:
                f, self.after = self.after, None
                f()
        elif self.phase == "foe_think":
            self.timer -= dt
            if self.timer <= 0:
                self.foe_act(self.current)
        elif self.phase == "exec" and self.script:
            self.timer -= dt
            while self.timer <= 0 and self.script:
                try:
                    self.timer += next(self.script)
                except StopIteration:
                    self.finish_action()

    # ------------------------------------------------------------------ draw
    def draw_world(self, surf):
        surf.blit(BACKGROUND, (0, 0))
        draw_torch(surf, self.t)
        mp = pygame.mouse.get_pos()
        for u in sorted(self.units, key=lambda u: u.pos.y):
            if self.state == "battle" and u is self.current and u.alive and self.phase != "victory":
                col = (90, 235, 130) if u.team == "hero" else (240, 90, 90)
                pulse = 1 + math.sin(self.t * 5) * 0.06
                ring = pygame.Surface((110, 36), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (*col, 70), (0, 0, 110, 36))
                pygame.draw.ellipse(ring, (*col, 230), (0, 0, 110, 36), 4)
                ring = pygame.transform.smoothscale(ring, (int(110 * pulse), int(36 * pulse)))
                surf.blit(ring, (u.pos.x - ring.get_width() / 2, u.pos.y - ring.get_height() / 2 - 4))
            u.draw(surf)
        # target markers
        if self.state == "battle" and self.phase == "target" and self.pending:
            vt = self.valid_targets(self.current, self.pending)
            for t in vt:
                hov = t.rect().collidepoint(mp)
                col = (255, 90, 90) if t.team != self.current.team else (90, 235, 130)
                w = 100 if hov else 90
                pygame.draw.ellipse(surf, col, (t.pos.x - w / 2, t.pos.y - 22, w, 30), 4 if hov else 2)
                ay = t.top_y() - 52 + math.sin(self.t * 8) * 4
                P(surf, col, [(t.pos.x, ay + 14), (t.pos.x - 10, ay), (t.pos.x + 10, ay)])
        for p in self.projs:
            p.draw(surf)
        for p in self.parts:
            a = max(0, 1 - p[4] / p[5])
            pygame.draw.circle(surf, p[6], (int(p[0]), int(p[1])), max(1, int(p[7] * a)))
        # hp bars
        for u in self.units:
            if not u.alive:
                continue
            w = 70 if u.boss else 56
            bx, by = u.pos.x + u.off.x - w / 2, u.top_y() - 16
            pygame.draw.rect(surf, (20, 10, 14), (bx - 2, by - 2, w + 4, 11), border_radius=3)
            pygame.draw.rect(surf, (95, 25, 35), (bx, by, w, 7), border_radius=2)
            pygame.draw.rect(surf, (225, 55, 70), (bx, by, w * u.hp / u.max_hp, 7), border_radius=2)
            icons = []
            if "stun" in u.status: icons.append(("Z", (255, 230, 90)))
            if "poison" in u.status: icons.append(("P", (120, 230, 120)))
            if u.guard: icons.append(("G", (150, 190, 255)))
            if "atk_up" in u.status: icons.append(("+A", (255, 190, 90)))
            if "atk_down" in u.status: icons.append(("-A", (230, 120, 230)))
            if "def_up" in u.status: icons.append(("+D", (150, 190, 255)))
            for i, (tt, cc) in enumerate(icons):
                txt(surf, tt, F_XS, cc, (bx + i * 22, by - 17))
        for tx in self.texts:
            f = font(tx["size"])
            a = 255 if tx["t"] < 0.9 else int(255 * (1.3 - tx["t"]) / 0.4)
            img = f.render(tx["s"], True, tx["col"])
            sh = f.render(tx["s"], True, (10, 8, 12))
            img.set_alpha(a)
            sh.set_alpha(a)
            r = img.get_rect(center=tx["p"])
            surf.blit(sh, r.move(2, 2))
            surf.blit(img, r)

    def draw_panel(self, u):
        pygame.draw.rect(screen, (22, 18, 16), (8, 8, 306, 104), border_radius=8)
        pygame.draw.rect(screen, (140, 105, 60), (8, 8, 306, 104), 3, border_radius=8)
        border = (90, 150, 255) if u.team == "hero" else (230, 90, 90)
        screen.blit(portrait(u.sprite, 82, border), (16, 16))
        txt(screen, u.name, F_M, WHITE, (106, 12))
        rows = [("heart", RED, u.hp, u.max_hp), ("drop", BLUE, u.mp, u.max_mp), ("bolt", ORANGE, u.focus, 100)]
        for i, (ic, col, v, mx) in enumerate(rows):
            if u.team == "foe" and i > 0:
                break
            y = 40 + i * 23
            draw_icon(screen, "heart" if ic == "heart" else ic, 114, y + 8, 8, WHITE)
            pygame.draw.rect(screen, (16, 12, 14), (128, y, 176, 17), border_radius=4)
            pygame.draw.rect(screen, tuple(int(c * .35) for c in col), (130, y + 2, 172, 13), border_radius=3)
            pygame.draw.rect(screen, col, (130, y + 2, 172 * max(0, v) / max(1, mx), 13), border_radius=3)
            txt(screen, f"{int(v)} / {int(mx)}", F_XS, WHITE, (216, y + 8), "center")
        if u.team == "foe":
            txt(screen, "Enemy turn" if not u.boss else "BOSS", F_S, (230, 120, 120), (128, 66))

    def draw_turn_bar(self):
        up = self.upcoming(8)
        if not up:
            return
        sizes = [54 if i == 0 else 40 for i in range(len(up))]
        total = sum(sizes) + 6 * (len(up) - 1) + 16
        x0 = W - 10 - total
        pygame.draw.rect(screen, (22, 18, 16), (x0, 8, total, 70), border_radius=8)
        pygame.draw.rect(screen, (140, 105, 60), (x0, 8, total, 70), 3, border_radius=8)
        x = x0 + 8
        for i, u in enumerate(up):
            sz = sizes[i]
            col = (90, 150, 255) if u.team == "hero" else (230, 90, 90)
            if i == 0:
                col = GOLD
            screen.blit(portrait(u.sprite, sz, col), (x, 8 + (70 - sz) // 2))
            x += sz + 6

    def draw_battle_ui(self):
        mp = V(pygame.mouse.get_pos())
        self.tip = None
        cur = self.current
        if cur and self.phase not in ("victory",):
            self.draw_panel(cur)
        else:
            self.draw_panel(self.heroes[0])
        self.draw_turn_bar()
        if self.banner_t > 0:
            f = F_M
            w = f.size(self.banner)[0] + 40
            a = min(1, self.banner_t / 0.4)
            ov = pygame.Surface((w, 38), pygame.SRCALPHA)
            pygame.draw.rect(ov, (14, 12, 14, int(190 * a)), (0, 0, w, 38), border_radius=10)
            screen.blit(ov, (W - 20 - w - 40 if w < 500 else 330, 92))
            txt(screen, self.banner, f, WHITE, ((W - 60 - w / 2) if w < 500 else 330 + w / 2, 111), "center")
        if self.hero_turn():
            u = self.current
            for i, (s, c) in enumerate(zip(u.skills, self.radial_centers(u))):
                hov = (mp - c).length() <= 28
                dis = not self.usable(u, s)
                badge = None
                bc = BLUE
                if s.focus:
                    badge, bc = s.focus, ORANGE
                elif s.mp:
                    badge = s.mp
                round_button(screen, (int(c.x), int(c.y)), 27, s.icon, hov, dis, badge, bc, selected=(self.pending is s))
                if hov:
                    self.tip = (s, c)
            for name, c in self.BOTTOM.items():
                s = SPECIALS[name]
                hov = (mp - V(c)).length() <= 28
        # bottom-left buttons (always visible)
        for name, c in self.BOTTOM.items():
            s = SPECIALS[name]
            hov = (mp - V(c)).length() <= 28
            dis = not self.hero_turn() or (name == "potion" and self.potions <= 0) or (name == "swap" and not self.valid_targets(self.current, s))
            badge = self.potions if name == "potion" else None
            round_button(screen, c, 27, s.icon, hov and not dis, dis, badge, (200, 60, 80), selected=(self.pending is s))
            if hov:
                self.tip = (s, V(c))
        for x, ic in ((W - 94, "menu"), (W - 44, "ff")):
            r = pygame.Rect(0, 0, 40, 40)
            r.center = (x, H - 34)
            hov = r.collidepoint(mp)
            pygame.draw.rect(screen, (28, 24, 24), r, border_radius=6)
            pygame.draw.rect(screen, GOLD if (hov or (ic == "ff" and self.fast)) else (160, 125, 75), r, 3, border_radius=6)
            draw_icon(screen, ic, r.centerx, r.centery, 11, WHITE)
        if self.phase == "target" and self.pending:
            txt(screen, f"{self.pending.name}: choose a target  (right-click to cancel)", F_S, GOLD, (W // 2, 140), "center")
        # tooltip
        if self.tip:
            s, c = self.tip
            lines = wrap(s.desc, F_XS, 230)
            meta = []
            if s.mp: meta.append(f"{s.mp} MP")
            if s.focus: meta.append(f"{s.focus} Focus")
            meta.append(TARGET_TEXT.get(s.target, ""))
            h = 30 + 16 * len(lines) + 22
            x = min(W - 262, max(8, c.x + 36))
            y = min(H - h - 8, max(100, c.y - h / 2))
            pygame.draw.rect(screen, (18, 14, 14), (x, y, 254, h), border_radius=8)
            pygame.draw.rect(screen, (150, 115, 65), (x, y, 254, h), 2, border_radius=8)
            txt(screen, s.name, F_S, GOLD, (x + 10, y + 6))
            for i, ln in enumerate(lines):
                txt(screen, ln, F_XS, WHITE, (x + 10, y + 30 + i * 16), shadow=False)
            txt(screen, "  |  ".join(meta), F_XS, (150, 200, 255), (x + 10, y + h - 20), shadow=False)
        # intro card
        if self.intro_t > 0:
            fl = FLOORS[self.floor]
            a = min(1, self.intro_t / 0.5, (2.6 - self.intro_t) / 0.4)
            ov = pygame.Surface((W, 150), pygame.SRCALPHA)
            ov.fill((0, 0, 0, int(190 * a)))
            screen.blit(ov, (0, 285))
            for s, f, c, y in ((f"FLOOR {self.floor + 1}", F_M, (200, 200, 220), 312),
                               (fl["name"], F_XL if len(fl["name"]) < 20 else F_L, GOLD, 355),
                               (f"Boss: {fl['boss']}", F_M, (240, 120, 120), 408)):
                img = f.render(s, True, c)
                img.set_alpha(int(255 * a))
                screen.blit(img, img.get_rect(center=(W // 2, y)))

    def perk_rects(self):
        return [pygame.Rect(90 + i * 270, 270, 250, 220) for i in range(3)]

    def overlay(self, a=170):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, a))
        screen.blit(ov, (0, 0))

    def draw(self):
        world = pygame.Surface((W, H))
        self.draw_world(world)
        world.blit(VIGNETTE, (0, 0))
        if self.state == "battle" and self.shake > 0:
            s = int(self.shake * 22)
            screen.fill((10, 8, 12))
            screen.blit(world, (random.randint(-s, s), random.randint(-s, s)))
        else:
            screen.blit(world, (0, 0))
        mp = pygame.mouse.get_pos()
        if self.state == "title":
            self.overlay(120)
            txt(screen, "GUILD OF CHAOS", F_XL, RED, (W // 2, 130), "center")
            txt(screen, "A turn-based tactics RPG  -  every floor has a different boss", F_M, WHITE, (W // 2, 190), "center")
            lines = ["Click a skill button (or press 1 / 2 / 3), then click a target.",
                     "Melee attacks can only hit the FRONT row. Ranged skills hit anyone.",
                     "Build FOCUS to unleash each hero's SPECIAL (3rd skill).",
                     "Defend, swap places or drink potions with the buttons bottom-left."]
            for i, l in enumerate(lines):
                txt(screen, l, F_S, (220, 220, 235), (W // 2, 560 + i * 24), "center")
            if int(self.t * 2) % 2 == 0:
                txt(screen, "Click or press ENTER to start", F_L, WHITE, (W // 2, 500), "center")
        elif self.state == "battle":
            self.draw_battle_ui()
        elif self.state == "reward":
            self.overlay(190)
            txt(screen, "BOSS DEFEATED!", F_XL, GOLD, (W // 2, 130), "center")
            txt(screen, "The party rests (+35% HP, +50% MP). Choose a perk:", F_M, WHITE, (W // 2, 200), "center")
            for r, (n, d, _) in zip(self.perk_rects(), self.perks):
                hov = r.collidepoint(mp)
                pygame.draw.rect(screen, (34, 28, 26) if not hov else (52, 42, 34), r, border_radius=10)
                pygame.draw.rect(screen, GOLD if hov else (150, 115, 65), r, 3, border_radius=10)
                txt(screen, n, F_L, GOLD, (r.centerx, r.y + 60), "center")
                for i, ln in enumerate(wrap(d, F_S, 200)):
                    txt(screen, ln, F_S, WHITE, (r.centerx, r.y + 120 + i * 22), "center")
        elif self.state == "gameover":
            self.overlay(200)
            txt(screen, "DEFEAT", F_XL, RED, (W // 2, 270), "center")
            txt(screen, f"Your party fell on floor {self.floor + 1}.", F_M, WHITE, (W // 2, 340), "center")
            txt(screen, "Click or press ENTER to return to the title", F_M, GOLD, (W // 2, 420), "center")
        elif self.state == "win":
            self.overlay(190)
            txt(screen, "VICTORY!", F_XL, GOLD, (W // 2, 250), "center")
            txt(screen, "The Lich King is destroyed. The dungeon is yours!", F_M, WHITE, (W // 2, 330), "center")
            txt(screen, "Click or press ENTER to return to the title", F_M, GOLD, (W // 2, 420), "center")
        if self.paused:
            self.overlay(200)
            txt(screen, "PAUSED", F_XL, GOLD, (W // 2, 200), "center")
            self.menu_rects = {}
            for i, (k, label) in enumerate((("resume", "Resume"), ("restart", "Restart run"), ("quit", "Quit game"))):
                r = pygame.Rect(W // 2 - 120, 290 + i * 70, 240, 52)
                self.menu_rects[k] = r
                pygame.draw.rect(screen, (50, 42, 36) if r.collidepoint(mp) else (30, 26, 24), r, border_radius=10)
                pygame.draw.rect(screen, GOLD, r, 3, border_radius=10)
                txt(screen, label, F_M, WHITE, r.center, "center")

    # ------------------------------------------------------------------- main
    def run(self):
        while True:
            dt = min(clock.tick(60) / 1000, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif e.type == pygame.KEYDOWN:
                    self.key(e.key)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    self.click(e.pos, e.button)
            self.update(dt)
            self.draw()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()