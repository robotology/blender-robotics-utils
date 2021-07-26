# Blender Robotics Utils
This repository contains utilities for exporting/controlling your robot in [Blender](https://www.blender.org/)

## Maintainers
This repository is maintained by:

| | |
|:---:|:---:|
| [<img src="https://github.com/Nicogene.png" width="40">](https://github.com/niNicogenecogene) | [@Nicogene](https://github.com/Nicogene) |

## Blender
### urdfToBlender
Python script that given the urdf of a robot as input, define the complete rig, in terms of bones, meshes and joint limits.
#### Dependencies
- Blender > 2.79
- [iDynTree](https://github.com/robotology/idyntree) python bindings
- `GAZEBO_MODEL_PATH` [properly set](https://github.com/robotology/icub-models#use-the-models-with-gazebo).
#### Usage
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

#### Examples

|**iCub 2.5** | **iCub 3**|
|:---:|:---:|
| ![immagine](https://user-images.githubusercontent.com/19152494/126991916-39b97bd1-da3b-4114-8597-9d835ad835a1.png) | ![immagine](https://user-images.githubusercontent.com/19152494/126991957-feb4eb6b-5ae0-4d3b-bfef-4ec05a5eaf10.png) |


#### Known limitations
- Only fixed or revolute joints are handled(see https://github.com/robotology/idyntree/issues/881, it requires iDynTree >= 3.3.0).
- Only `.stl` and `.ply` format are supported for meshes.

### blenderController 🚧
Simple demo script that opens a [YARP `remote_controlboard`] for controlling the iCub head, and attach to the animations frames a callback for moving the joints accordingly to the movements of the rig.
Since it is script that has been created with the purpose to show the potentialities of Blender in robotics, this will be not improved/extended or maintained.
Here is a video showing this simple controller on iCub.

https://user-images.githubusercontent.com/19152494/125633637-26f74b75-390b-409e-bde1-d1e326f50c23.mp4

### blenderRCBPanel 🚧
WORK IN PROGRESS

