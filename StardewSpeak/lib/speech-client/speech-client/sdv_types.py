from __future__ import annotations
from typing import TypedDict, Any, Literal, NotRequired

class PlayerStatus(TypedDict):
    location: str
    position: tuple[float, float]
    facingDirection: int
    isMoving: bool
    tileX: int
    tileY: int
    canMove: bool

type ToolStatus = Tool | None

class BaseGameItem(TypedDict):
    type: Literal[""]
    netName: str
    stack: int

class Tool(BaseGameItem):
    type: Literal["tool"]
    isTool: True
    power: int
    baseName: str
    upgradeLevel: int
    tileX: int
    tileY: int

class MeleeWeapon(BaseGameItem):
    type: Literal["meleeWeapon"]

class Scythe(BaseGameItem):
    type: Literal["scythe"]

type GameItem = Tool | MeleeWeapon | Scythe

class ClickableComponent(TypedDict):
    containsMouse: bool
    visible: bool
    center: Point
    focusTarget: NotRequired[Point]

type Point = tuple[int, int]