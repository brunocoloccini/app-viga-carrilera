# section_core

`section_core` is a Python core library for structural section modeling and property workflows. It is intended to be reused by future applications for crane runway beams, steel beams, steel columns, built-up columns, and arbitrary structural sections.

This repository currently contains only the initial scaffold and the first units subsystem.

## Install (editable mode)

```bash
pip install -e .
```

From this repository, run that command inside `engineering-core/`.

## Run tests

```bash
pytest
```

## Why units are mandatory

Structural calculations are highly sensitive to unit consistency. The units module enforces explicit units at input, validates dimensional compatibility, and converts to internal canonical units for computation. This helps prevent silent errors such as mixing stress/force, mass/weight, or geometry/property dimensions.
