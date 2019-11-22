from helpers import *


class Annotation:
    def __init__(self, imageName: str = None, width: int = None, height: int = None, boxes: [] = None):
        self.imageName = imageName
        self.width = width
        self.height = height
        self.boxes = boxes


class Box:
    def __init__(
            self, lowerRightX: int = None, lowerRightY: int = None,
            upperRightX: int = None, upperRightY: int = None):
        self.lowerRightX = lowerRightX
        self.lowerRightY = lowerRightY
        self.upperRightX = upperRightX
        self.upperRightY = upperRightY
