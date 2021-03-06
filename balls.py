from __future__ import annotations

import decimal
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, Optional
from collections import deque
PEAK_FACTOR=1.5

@dataclass
class Coords:
    x: float = 0.0
    y: float = 0.0

    def to_tuple(self) -> Tuple[int, int]:
        """ Returns these coordinates as a pair of integers for OpenCV. """
        return int(self.x), int(self.y)

    def __str__(self):
        trunc = lambda v: decimal.Decimal(str(v)).quantize(decimal.Decimal('.0'), rounding=decimal.ROUND_DOWN)
        return f'({trunc(self.x)}, {trunc(self.y)})'


@dataclass
class MovementVector:
    xvel: float = 0.0

    yvel: float = 0.0

    def average(self, new_x, new_y, alpha_factor):
        self.xvel = alpha_factor * self.xvel + (1-alpha_factor) * new_x
        self.yvel = alpha_factor * self.yvel + (1-alpha_factor) * new_y

    def caught(self):
        self.xvel = 0
        self.yvel = 0
    def is_peak(self):
        if abs(self.yvel) < PEAK_FACTOR:
            return True
        else:
            return False



class Circle:
    coords: Coords
    """ 
    The current position of the circle in the plane perpendicular to the observer's line of sight. The plane is defined
    such that a higher X-coordinate means the circle is moving right relative to the observer, and a higher Y-coordinate
    means the circle is moving upwards (against gravity) in physical space.
    """

    radius: float
    """ The radius of the circle, in pixels. """

    def __init__(self, coords, radius):
        self.coords = coords
        self.radius = radius

    def intersects(self, c2: Circle, fuzzy_factor=1.0) -> bool:
        return math.sqrt((self.coords.x - c2.coords.x) ** 2 + (self.coords.y - c2.coords.y) ** 2) \
               <= (self.radius + c2.radius) * fuzzy_factor





class Ball:
    """ Data representation of a physical juggling ball. """

    class State(Enum):
        """ The ball's state in the juggling cycle. """
        JUMPSQUAT = auto()
        AIRBORNE = auto()
        CAUGHT = auto()
        UNDECLARED = auto()

    class ThrowState(Enum):
        LEFTRISING = auto()
        RIGHTRISING = auto()
        LEFTFALLING = auto()
        RIGHTFALLING = auto()
        UNRECOGNIZED = auto()
    name: str
    """ An identifier for this ball instance. Only used for debugging purposes. """

    movement: MovementVector
    "Whether the ball is at the apex of its arc or not, defined by y velocity"
    peak: bool = False

    """
    The last-recorded movement vector for this ball. Defined such that a direction of 0 radians equates to movement
    to the right relative to the observer.
    """

    circle: Optional[Circle] = None
    """ 
    The circle represnting this ball's position. The radius of the circle refers to the last-deteced radius of the blob 
    assigned to this ball from OpenCV. A value of `None` means that no blob is mapped to this ball.
    """

    state: State = State.UNDECLARED
    """ The ball's current state in the juggling cycle. """
    throwstate: ThrowState = ThrowState.UNRECOGNIZED

    found: bool = False
    """ Whether this ball has been mapped to a blob from the current frame. Used in the blob detection process. """

    jumpPoint: Optional[Coords] = None
    """ The location at which the ball first appeared after being caught. """

    trail_x: deque
    trail_y: deque

    def __init__(self, name: str):
        name = name.strip()
        if len(name.split()) > 1:
            raise ValueError('Ball name cannot contain whitespace')

        self.name = name
        self.movement = MovementVector()
        self.trail_x = deque([], maxlen=10)
        self.trail_y = deque([], maxlen=10)

    def __str__(self):
        return f'{self.name}({self.coords.x, self.coords.y})'


    #Series of functions for ThrowState
    def is_rising(self):
        if self.throwstate == self.ThrowState.LEFTRISING or self.throwstate == self.ThrowState.RIGHTRISING:
            return True
        else:
            return False
    def is_falling(self):
        if self.throwstate == self.ThrowState.LEFTFALLING or self.throwstate == self.ThrowState.RIGHTFALLING:
            return True
        else:
            return False
    def peaked(self):
        if self.throwstate == self.ThrowState.LEFTRISING:
            self.throwstate = self.ThrowState.LEFTFALLING
        elif self.throwstate == self.ThrowState.RIGHTRISING:
            self.throwstate = self.ThrowState.RIGHTFALLING
