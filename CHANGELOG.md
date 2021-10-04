# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Added action for automatically generate the rigs every time a commit
  is made in [`icub-models`](https://github.com/robotology/icub-models)

### `urdfToBlender`

- Added the support in urdfToBlender for the basic geometries
- Added the possibility to run it headless.

### `rigs`

- Added `iCubBlenderV2_5_visuomanip.blend`.

### `blenderRCBPanel`

- Added changes for controlling iCub hands.

## [0.1.0] - 2021-08-30

- Added `blenderRCBPanel` python script that spawns a panel for controlling parts of
  the robot(for now tested only with iCub).
- Added `urdfToBlender` python script that creates a rig starting from a urdf of a robot.
- Added `iCubBlenderV2_5.blend` and `iCubBlenderV3.blend`.
