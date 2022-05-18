# Frequentely Asked Questions

## How can I edit the speed of an animation?

After setting the keyframes of your animation, you can change the `animation speed` acting on the keyframes visible in the `Dope Sheet` panel.
The `Dope Sheet` panel gives you a complete overview of the keyframes and the joints involved in the animation. You can access the `Dope Sheet` panel from the top left menu called `Editor Type`, select `Animation` -> `Dope Sheet`.
If you click on the keyframes in the `iCub` or `iCubAction` rows you will select the keyframes for all the joints. You can refine the keyframe for the single joint by clicking on the corresponding row.

- The keyframes will appear yellow when they are selected, and white when de-selected.
- You will de-select the keyframes by clicking anywhere inside the timeline.
- Select with the mouse the desired keyframe.
- To select multiple keyframes, select the keyframes and press `Shift` at the same time.
- To select all the keyframes press `A`.
- If you drag the keyframe toward left or right you will change the animation speed relative to the selected keyframe.
- To move multiple keyframes, select the keyframes you want to move and press `G`.
- To scale the selected keyframe press `S`.
- To extend the time between two keyframes, select all the keyframes (press `A`) place the mouse cursor between two keyframes, and press `E`.


The following video shows some of the operations described above.


https://user-images.githubusercontent.com/19833605/168836359-5c2158c9-cbb2-40d0-9231-21f5baad3cf4.mp4

## How can I edit the trajectory shape of the animation?

You can also adjust the animation curves through the `Graph Editor`. The Graph Editor displays all the trajectory curves for the animation of all the joints. You can modify the animation of the single joint to have a refined behavior. You can access the Graph Editor panel from the top-left menu `Editor Type`, select `Animation` -> `Graph Editor`.

- You can select the joint you want to modify from the `3D Viewport` window, the Graph Editor will display the curves the joint follows during the animation. You can directly modify the curve by dragging and dropping the keyframe.
- If you select the entire robot from the `3D Viewport` window (press `A`) you will see all the curves that the joints follow, again select a keyframe and you will modify the curve for all the joints.
- You can also modify the curve for the single keyframe by selecting a keyframe from the `Timeline` pane, right-click with the mouse button, choosing `Interpolation Mode`, and then choosing the desired effect.

The following video shows some of the operations described above.

https://user-images.githubusercontent.com/19833605/168836429-bf6d2f1f-cd3e-456c-bddc-c8fcc8a625dc.mp4
