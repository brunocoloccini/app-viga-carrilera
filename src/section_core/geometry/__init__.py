"""Geometry subsystem for section_core."""

from .coordinate_frame import CoordinateFrame
from .errors import (
    CoordinateFrameError,
    DegenerateGeometryError,
    GeometryError,
    GeometryMergeError,
    InvalidToleranceError,
    UnsupportedCoordinateFrameError,
)
from .node import Node
from .point import Point2D
from .section_line import SectionLine
from .section_point import SectionPoint
from .tolerance import GeometryTolerance
from .transform import Transform2D

__all__ = [
    "CoordinateFrame",
    "CoordinateFrameError",
    "DegenerateGeometryError",
    "GeometryError",
    "GeometryMergeError",
    "GeometryTolerance",
    "InvalidToleranceError",
    "Node",
    "Point2D",
    "SectionLine",
    "SectionPoint",
    "UnsupportedCoordinateFrameError",
    "Transform2D",
]
