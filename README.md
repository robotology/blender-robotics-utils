# Blender Robotics Utils
This repository contains utilities for exporting/controlling your robot in [Blender](https://www.blender.org/)

![ezgif com-gif-maker](https://user-images.githubusercontent.com/19152494/128324719-b9bda13d-92dd-49f5-b866-8dd04b3f9d76.gif)

## Maintainers
This repository is maintained by:

| | | |
|:---:|:---:|:---:|
 [<img src="https://github.com/Nicogene.png" width="60">](https://github.com/niNicogenecogene) | [@Nicogene](https://github.com/Nicogene) | <img src="https://user-images.githubusercontent.com/4537987/134487985-e66b9dae-767d-4c3b-9ce1-9e6fb19cf07a.png" width="200"> |


## Addons installation
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

### Installation
The addons can be installed by running the following command:
```console
conda activate blenderenv
cd blender-robotics-utils/script
blender -b --python-use-system-env -P ./addons_installer.py
```

## urdfToBlender
Panel/Python script that given the urdf of a robot as input, define the complete rig, in terms of bones, meshes and joint limits.


### Usage with GUI

Once installed correctly the dependencies run:

(Windows Powershell)
```
 & "C:\Program Files\Blender Foundation\Blender <blender_version>\blender.exe" --python-use-system-env
```
(Linux & macOs)
```
$ blender --python-use-system-env
```

If the installation went fine you should have this panel on the right under the `Tools` section:

![immagine](https://user-images.githubusercontent.com/19152494/154102335-76c5312a-81ea-46b5-92cc-93d0668596e7.png)

After clicking "Select the urdf" it will be opened a file browse such as:

![immagine](https://user-images.githubusercontent.com/19152494/126337119-6b899183-1f2a-413c-8b88-4e5727818891.png)

After selecting the urdf, the script creates the rig of the robot in term of armature and meshes.

### Usage without GUI

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


## blenderRCBPanel 🚧
Python addon that consists in a panel inside the pose mode for connecting parts of the rig to the parts of the real robot(or simulator).

If the installation went fine you should have this panel on the right under the `Tools` section.
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

### Joint space

It is possible to define the animation changing the values of joints from the joints' list, every time a new value is entered a waypoint in the animation is setted.

Video 🎥:

https://user-images.githubusercontent.com/19833605/159922346-0bc9cd53-1a5a-4ea1-a7f7-453bdbdc1547.mp4

### Cartesian space
#### Reach target
1. The user selects the `Base Frame` and the `End Effector Frame` according to the joint he/she wants to move.
2. Input the tranformation to be reached by `End Effector Frame` respect to `Base Frame`, in XYZ(meters) and RPY(degrees).
3. Press `Reach target` button.
4. The waypoint in the animation is automatically set.

Video 🎥:

https://user-images.githubusercontent.com/19152494/165498930-224c3871-620a-4c6c-9162-7e30c3578265.mp4

#### Drag & Drop
1. The user selects the `Base Frame` and the `End Effector Frame` according to the joint he/she wants to move.
2. Press the button `Drag & Drop` to activate the feature. Once the button is pressed the user loses control of Blender.
3. The user moves the mouse pointer in the 3D space of Blender and clicks the `right mouse button` to drop the position.
4. The user clicks on the `left mouse button` to deactivate the drag and drop feature and to bring back the control to Blender.
5. The waypoint in the animation is automatically set.

Video 🎥:

https://user-images.githubusercontent.com/19833605/167880668-5176a0c1-3110-41dc-be9f-8e0565752430.mp4


### Known limitations

- We are controlling sequentially all the parts connected, this may lead to some discrepancies between the animation and the movements. This can be improved using multithreading and/or using a remapper.

## FAQs 🙋‍♂️

Check our [faq section]() 👈
