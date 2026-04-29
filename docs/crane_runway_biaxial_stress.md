# Crane runway elastic biaxial stress (V1-029)

## Purpose
This module combines elastic normal stress from:
- vertical bending moment `My` about the strong axis, and
- lateral bending moment `Mz` about the weak axis,

at representative section corner fibers for crane runway beams.

## Stress points
The result is reported at four points:
- `top_left`
- `top_right`
- `bottom_left`
- `bottom_right`

## Sign convention
- Tension is positive.
- Compression is negative.
- Positive vertical sagging moment produces:
  - top compression, and
  - bottom tension.
- Lateral moment produces opposite signs on left/right fibers with:
  - `sigma_l_left = +Mz / S_z_left`
  - `sigma_l_right = -Mz / S_z_right`

Combined stress at each point is `sigma_total = sigma_vertical + sigma_lateral`.

## Scope and non-scope
This feature performs stress calculation only (gross elastic section behavior).

It does **not** include:
- CIRSOC/CISC/AISC code checks,
- resistance checks,
- allowable stress checks,
- fatigue checks,
- lateral-torsional buckling checks,
- torsion,
- rail eccentricity,
- local stress effects.
