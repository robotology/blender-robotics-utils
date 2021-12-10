# Blender Robotics Utils
This repository contains utilities for exporting/controlling your robot in [Blender](https://www.blender.org/)

![ezgif com-gif-maker](https://user-images.githubusercontent.com/19152494/128324719-b9bda13d-92dd-49f5-b866-8dd04b3f9d76.gif)

## Maintainers
This repository is maintained by:

| | | |
|:---:|:---:|:---:|
 [<img src="https://github.com/Nicogene.png" width="60">](https://github.com/niNicogenecogene) | [@Nicogene](https://github.com/Nicogene) | <img src="https://user-images.githubusercontent.com/4537987/134487985-e66b9dae-767d-4c3b-9ce1-9e6fb19cf07a.png" width="200"> |


## urdfToBlender
Python script that given the urdf of a robot as input, define the complete rig, in terms of bones, meshes and joint limits.
### Dependencies
- Blender > 2.79
- [iDynTree](https://github.com/robotology/idyntree) python bindings
- `GAZEBO_MODEL_PATH` [properly set](https://github.com/robotology/icub-models#use-the-models-with-gazebo).

An easy way to install the dependencies is to use the [conda](https://docs.conda.io/en/latest/) binaries packages.
Just [install conda](https://github.com/robotology/robotology-superbuild/blob/master/doc/install-miniforge.md) and then:

```
conda create -n blenderenv
conda activate blenderenv
conda install -c conda-forge -c robotology python=<blender_py_ver> yarp idyntree
conda env config vars set PYTHONPATH=/where/the/bindings/are/installed
```
where `<blender_py_ver>` is the python version used inside Blender.

### Usage

#### With GUI

Once installed correctly the dependencies run:

(Windows Powershell)
```
 & "C:\Program Files\Blender Foundation\Blender <blender_version>\blender.exe" --python-use-system-env
```
(Linux & macOs)
```
$ blender --python-use-system-env
```

Go to "Scripting" section, open `urdfToBlender`, then run.
It will open a dialog for selecting the urdf to be converted to rig.

![immagine](https://user-images.githubusercontent.com/19152494/126337119-6b899183-1f2a-413c-8b88-4e5727818891.png)

After selecting the urdf, the script creates the rig of the robot in term of armature and meshes.

#### Without GUI

It is also possible to run this script from the command line interface, in this case you have to specify the `urdf_fiename`
to be converted and optionally the `blend_filename` to be saved(by default it saves `robot.blend` in the current directory).

(Windows Powershell)
```
 "C:\Program Files\Blender Foundation\Blender <blender_version>\blender.exe" --python-use-system-env -b -P "C:\where\you\have\blender-robotics-utils\script\urdfToBlender.py" -- --urdf_filename "C:\where\you\have\model.urdf" --blend_filename "C:\where\you\want\to\save\myrobot.blend"

```
(Linux & macOs)
```
$ blender --python-use-system-env -b -P "/where/you/have/blender-robotics-utils/script/urdfToBlender.py" -- --urdf_filename "/where/you/have/model.urdf" --blend_filename "/where/you/want/to/save/myrobot.blend"
```

### Examples

|**iCub 2.5** | **iCub 3**|
|:---:|:---:|
| ![immagine](https://user-images.githubusercontent.com/19152494/126991916-39b97bd1-da3b-4114-8597-9d835ad835a1.png) | ![immagine](https://user-images.githubusercontent.com/19152494/126991957-feb4eb6b-5ae0-4d3b-bfef-4ec05a5eaf10.png) |


### Known limitations
- Only fixed or revolute joints are handled(see https://github.com/robotology/idyntree/issues/881, it requires iDynTree >= 3.3.0).
- Only `.stl`, `.ply` and `.dae` format are supported for meshes.

## iCubNeckBlenderController 🚧
Simple demo script that opens a [YARP `remote_controlboard`](http://yarp.it/latest/classRemoteControlBoard.html#details) for controlling the iCub head, and attach to the animations frames a callback for moving the joints accordingly to the movements of the rig.
Since it is script that has been created with the purpose to show the potentialities of Blender in robotics, this will be not improved/extended or maintained.
Here is a video showing this simple controller on iCub.

https://user-images.githubusercontent.com/19152494/125633637-26f74b75-390b-409e-bde1-d1e326f50c23.mp4

## blenderRCBPanel 🚧
Python script that creates a panel inside the pose mode for connecting parts of the rig to the parts of the real robot(or simulator).
For using it follow [the instructions like the other scripts](https://github.com/robotology/blender-robotics-utils#usage) open `blenderRCBPanel` and the run it.
If every went fine you should have this panel on the right under the `Tools` section.
First of all you have to configure it loading a `.json` file representing the structure of your robot like this one:
```json
{
    "parts": [
        ["torso", "Torso"],
        ["head", "Head"],
        ["left_arm", "Left arm"],
        ["right_arm", "Right arm"],
        ["left_leg", "Left leg"],
        ["right_leg", "Right leg"]
    ]
}

```
It should contain a list of pair where the first value will be the "YARP name" of the part, and the second one will be the name displayed in the list.
Once configured, select the parts you want to control, press connect and then have fun!
This has been tested with `iCub 2.5`.

https://user-images.githubusercontent.com/60427731/145424773-e17e29b9-2229-4d3c-8f5e-fe40bd7725b6.mp4

### Known limitations
- We are assuming that the robot has these 5 parts:
  - `head`
  - `torso`
  - `left_arm`
  - `right_arm`
  - `left_leg`
  - `right_leg`
- We are controlling sequentially all the parts connected, this may lead to some discrepancies between the animation and the movements. This can be improved using multithreading and/or using a remapper.

