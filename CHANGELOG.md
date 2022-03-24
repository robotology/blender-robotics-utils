# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### `blenderRCBPanel`

- Added list of controllable joints for designing animations.

## [0.3.0] - 2022-02-28

### `addons_installer`

- Added python script for installing and enabling the blender addons of this
  repository.

### `urdfToBlender`

- Code refactored for displaying the converter as panel that can be installed as addon.

### `blenderRCBPanel`

- Added robot's parts configuration through a JSON file structured as the [proposed template](https://github.com/robotology/blender-robotics-utils/blob/master/script/conf/parts.json)
- Code refactored to be able to display the panel in the list of add-ons of blender

## [0.2.0] - 2021-11-29
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
