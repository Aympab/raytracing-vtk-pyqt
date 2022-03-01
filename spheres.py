import numpy as np
import vtk

renderer = vtk.vtkRenderer()
renderer.SetBackground(0.3, 0.4, 0.5)

render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)

for sphere_index in range(10):
    source = vtk.vtkSphereSource()
    
    x = -5.+10.*np.random.random()
    y = -5.+10.*np.random.random()
    z = -5.+10.*np.random.random()
    radius = 0.5+0.5*np.random.random()
    
    source.SetRadius(radius)
    source.SetCenter(x, y, z)
    source.SetPhiResolution(21)
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    
    rgb = 0.4 + 0.6*np.random.random(3)
    actor.GetProperty().SetDiffuseColor(*rgb)
    actor.GetProperty().SetDiffuse(0.8)
    actor.GetProperty().SetSpecular(0.5)
    actor.GetProperty().SetSpecularColor(1.,1.,1.)
    actor.GetProperty().SetSpecularPower(30.)
    
    renderer.AddActor(actor)
    
render_window.SetSize(800, 800)
interactor.Initialize()
render_window.Render()
interactor.Start()