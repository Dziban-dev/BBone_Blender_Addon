BBONE | Blender Addon

![Baner](https://github.com/Dziban-dev/BBone_Blender_Addon/blob/main/BBone.png)

## What is BBone

BBone is an addont aimed at helping with the creation of base meshes used for sculping , Think of BSpheres but free.

The addon itself it's a Fork from Sculpt Tools anfeo found here: (https://github.com/anfeo) A [GitHub - anfeo/Blender-Sculpt-Tools: Blender Sculpt tools](https://github.com/anfeo/Blender-Sculpt-Tools) ,I just streamed lined it a bit, added some new cool features, and I'm planning on adding more in the near future.

## How to use?

[![Watch the video](https://img.youtube.com/vi/t90QsF38ldc/hqdefault.jpg)](https://youtu.be/t90QsF38ldc)

## New Version! v 1.1

- Corrected bugs when remeshing BBone Skin meshes.
- Major refactor to BBone Skin meshes, so they now more closely resamble the BBone armature shapes.
- Minor improvements.
### v 1.1.1
- Corrected an error where BBone Armatures not positioned at the world origin would not be re-meshed correctly.
- Corrected a bug that would cause the 3D_View mode set to Edit_Mode after updating a BBone Armature linked to a BBone Skin.
- Fixed a bug that would cause an error when trying to re-mesh a BBone Skin with a disabled modifier. 

### v 1.1.2
 - Fixed error with re-mesh operator when trying to remesh BBone Skins, preventing it from adding the final subdivision modifier. 

## New features! v 1.0

- The UI is reponsive and displays only the necesary elements acording to your selection.
  
- You can now link and unlink BBone Mesh from BBone Armature.
  
- You can link or relink BBone armatures by selecting the armature and the mesh targe or the other way around.
  
- You can now symetrize selected bones over the X axis on Edit Mode.
  
- You can one click remesh your base mesh once it is ready, it will automatically unlink it from the BBone Armature, Remesh and send you to Sculpt Mode.
  

## Upcomming features

- Having a library of predefined base BBone armatures, like Hands, limbs, claws etc.
  

## How to install

1. Download the .py file from the repository.
  
2. Open Blender and go into Preferences.
  
3. Navigate to the Addon sections, click install and search for the .py file you just downloaded.
  
4. Enable the addon by ticking the checkbox.
