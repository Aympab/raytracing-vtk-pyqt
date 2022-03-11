# Visu raytracing
Scientific data visualisation project.
Using online and offline rendering modes with vtraytracing.

This documents contains the presentation of our work on implementing a
RayTracing algorithm using the VTK library and Python's bindings.

First, we are going to do a brief sate of the art on raytracing, then we will
explain our implementation logic and technical choices. To conclude, we will
show some images rendered by our application.

# Running the code
You can use the `environment.yml` file to setup your Python environment with
conda.

## Required librairies
vtk9
qt

To run the app, just launch the `main.py` file and let the UI guide you !


# Brief state of the art
Ray tracing was first introduced in 1980 by Turner Whitted in his paper on
[An Improved Illumination Model for Shaded Display](https://www.cs.drexel.edu/~david/Classes/Papers/p343-whitted.pdf)

This is one of the picture presented in T. Whitted's paper, the rendering time **74 minutes**.

![Whitted Ray Tracing](fig/figureWhitted74min.png)

Since then, a few methods of ray tracing have emmerged, and our hardware too,
gains in computational power every year. Now, we are able to compute raytracing
in real time with GPU accelerators.

Here is the different methods that have emmerged since the first paper on the
ray-tracing algorithm :
- **Path Tracing** : Ray tracing but with only 1 random ray bouncing, then
sample (average) a certain amount of them
- **Bidirectionnal Path Tracing** : From camera to objects and from light source
to objects. Less variance of the result in complicated bouncing scenarios
- **Volumetric Path Tracing** : Samples a distance before an object is touched,
and scatters the light at this point (used to render fog, fire, particles...)
- **Metropolis Light Transport** : BDPT but the sampling is not totally random,
it explores nearby light paths with as the metropolis algorithm explores
distributions
- **Photon Mapping** : Used a lot for caustics, reflection, interreflection and
translucent surfaces

In this program, we used the **path tracing** method to compute our offline
rendering.

# Implementation Logic
## Python's VTK bindings

## Usef Interface : Qt & Qt Designer
    We decided to use Qt (with either PySide or PyQt as a python wrapper) for
the User interface, this way, we don't have to make complex documentation about
what keyboard shortcut to use to interact with our VTK panel.

![UI Light sliders](fig/lightSlidersUI.png)

To build the UI we used [Qt Designer](https://doc.qt.io/qt-5/qtdesigner-manual.html),
which generates a `.ui` file. This file is compiled at the start of our
program into a `.py` python file which is the corresponding Qt Windows, with all
sizes and objects' labels automatically set. We do not have to touch this file
once it is generated. This method allowed us to make a more complex UI to give
the user more interaction with our VTK environment.

# Ameliorations
- Parallelize the main RTX loop (maybe in another language)
- Add different sources of light
- Add different RTX rendering methods

# Usefull websites
https://github.com/RayTracing/raytracing.github.io
https://pyscience.wordpress.com/2014/10/05/from-ray-casting-to-ray-tracing-with-python-and-vtk/
http://www.lama.univ-savoie.fr/pagesmembres/lachaud/Cours/INFO805/Tests/html/ig_tp2.html
https://medium.com/swlh/ray-tracing-from-scratch-in-python-41670e6a96f9
https://github.com/RichCartwright/Path-Tracing-Viz
