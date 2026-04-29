# Coordinate System Manager

The geometry subsystem provides translation-only 2D coordinate support in the section y-z plane.

## Core models

- `Point2D` stores `y_internal_mm` and `z_internal_mm`.
- `Node` stores selectable node metadata and internal y/z coordinates.
- `CoordinateFrame` supports translation-only coordinate transforms.

## Origin modes

- Fixed origin.
- Node origin (linked or frozen).
- Centroid origin (dynamic or frozen).

## Transforms

- `internal_to_local(y_internal_mm, z_internal_mm)`
- `local_to_internal(y_local, z_local, units="mm")`
- `origin_internal()`

## Rotation

Any nonzero rotation is currently unsupported and raises `UnsupportedCoordinateFrameError`.
