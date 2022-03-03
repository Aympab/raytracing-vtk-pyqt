from hashlib import new
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QObject
from readVTP import *
import webbrowser
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkSkybox,
    vtkTexture
)
from vtk import vtkPNGReader, vtkJPEGReader, vtkTextureMapToSphere
from utils import *
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

model = "models/Nuclear_Power_Plant_v1/10078_Nuclear_Power_Plant_v1_L3.obj"
# scene = "models/naboo/naboo_complex.obj"

class ViewersApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(ViewersApp, self).__init__()
        self.vtk_widget = None
        self.ui = None
        self.setup()
        
    def setup(self):
        import Mini_app_Qt_VTK
        self.ui = Mini_app_Qt_VTK.Ui_MainWindow()
        self.ui.setupUi(self)
        self.vtk_widget = QMeshViewer(self.ui.vtk_panel)
        self.ui.vtk_layout = QtWidgets.QHBoxLayout()
        self.ui.vtk_layout.addWidget(self.vtk_widget)
        self.ui.vtk_layout.setContentsMargins(0,0,0,0) #left, up, right, down
        self.ui.vtk_panel.setLayout(self.ui.vtk_layout)
        
        self.ui.comboBox.activated.connect(self.vtk_widget.Switch_Mode)
        self.ui.Resolution.valueChanged.connect(self.vtk_widget.set_Resolution)
        self.ui.radioButton.clicked.connect(self.vtk_widget.button_event)
        self.ui.saveButton.clicked.connect(self.vtk_widget.save_event)
        
        self.ui.lightIntensity.valueChanged.connect(self.vtk_widget.light_intensity)
        self.ui.lightPos_x.valueChanged.connect(self.vtk_widget.light_pos_x)
        self.ui.lightPos_y.valueChanged.connect(self.vtk_widget.light_pos_y)
        self.ui.lightPos_z.valueChanged.connect(self.vtk_widget.light_pos_z)
        
    def initialize(self):
        self.vtk_widget.start()

class QMeshViewer(QtWidgets.QFrame):
    def __init__(self, parent):
        super(QMeshViewer, self).__init__(parent)
        
        interactor = QVTKRenderWindowInteractor(self)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(interactor)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        
        #https://lorensen.github.io/VTKExamples/site/Python/GeometricObjects/Sphere
        colors = vtk.vtkNamedColors()





        # Scene
        # naboo_actor = actorFromFile(scene)

        # Powerplant
        powerplant_mapper, powerplant_actor = modelFromFile(model)

        # renderer = vtk.vtkOpenGLRenderer()
        renderer = vtk.vtkRenderer()
        render_window = interactor.GetRenderWindow()
        render_window.AddRenderer(renderer)
        interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        render_window.SetInteractor(interactor)


        transform = vtkTransform()
        transform.Translate(1.0, 0.0, 0.0)

        axes = vtkAxesActor()
        #  The axes are positioned with a user transform
        axes.SetUserTransform(transform)
        
        renderer.AddActor(axes)
        #renderer.AddActor(actor)
        # renderer.AddActor(naboo_actor)
        renderer.AddActor(powerplant_actor)
        renderer.SetBackground(colors.GetColor3d("DarkGreen"))

        ## LIGHT
        self.light1 = vtk.vtkLight()
        self.light1.SetIntensity(0.5)
        self.light1.SetPosition(1000, 100, 100)
        self.light1.SetDiffuseColor(1, 1, 1)
        renderer.AddLight(self.light1)
        
        ## SUN BALL TO SHOW WHERE IS LIGHT
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(1000, 100, 100)
        sphereSource.SetRadius(10.0)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(colors.GetColor3d("Yellow"))
        actor.GetProperty().SetRepresentation(2)
        # actor.GetProperty().SetOpacity(0.001)
        renderer.AddActor(actor)
        self.actor = actor


        self.render_window = render_window
        self.interactor = interactor
        self.renderer = renderer
        self.sphere = sphereSource
        self.power_plant = powerplant_actor

        pSource = [0.0, -10, 0.0]
        pTarget = [500.0, 0.0, 200.0]
        
        addPoint(renderer, pSource, color=[1.0, 0.0, 0.0])
        addPoint(renderer, pTarget, color=[0.0, 1.0, 0.0])
        addLine(renderer, pSource, pTarget)
        # vtk_show(renderer)
        
    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    def Switch_Mode(self, new_value):
        self.actor.GetProperty().SetRepresentation(new_value)
        self.power_plant.GetProperty().SetRepresentation(new_value)
        self.render_window.Render()

    def button_event(self, new_value):
        print("Changing texture...")
        
        reader = vtkJPEGReader()
        reader.SetFileName("skin.jpg")
        texture = vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        
        # if new_value:
            # texture = vtkTexture()
        # else:
            # texture = vtkTexture()

        self.power_plant.SetTexture(texture)


    def set_Resolution(self, new_value):
        self.sphere.SetPhiResolution(new_value)
        self.sphere.SetThetaResolution(new_value)
        
        # self.power_plant.SetPosition(new_value, new_value, new_value)
        # self.light1.SetIntensity(new_value)
        
        self.render_window.Render()

    def light_pos_x(self, new_value):
        y = self.light1.GetPosition()[1]
        z = self.light1.GetPosition()[2]
        
        self.light1.SetPosition(new_value, y, z)
        self.sphere.SetCenter(new_value, y, z)
        self.render_window.Render()
        
        
    def light_pos_y(self, new_value):
        x = self.light1.GetPosition()[0]
        z = self.light1.GetPosition()[2]
        
        self.light1.SetPosition(x, new_value, z)
        self.sphere.SetCenter(x, new_value, z)
        self.render_window.Render()
        
    def light_pos_z(self, new_value):
        x = self.light1.GetPosition()[0]
        y = self.light1.GetPosition()[1]
        
        self.light1.SetPosition(x, y, new_value)
        self.sphere.SetCenter(x, y, new_value)
        self.render_window.Render()
        
    def light_intensity(self, new_value):
        self.light1.SetIntensity(new_value/100.)
        self.render_window.Render()
        

    def save_event(self):
        print(self.light1.GetFocalPoint())
        # self.light1.SetFocalPoint((100,100,100))
        
        print("Button pressed ! Saving...")

if __name__ == "__main__":
    with open("Mini_app_Qt_VTK.ui") as ui_file:
        with open("Mini_app_Qt_VTK.py", "w") as py_ui_file:
            uic.compileUi(ui_file, py_ui_file)

    app = QtWidgets.QApplication(["Application-RTX"])
    main_window = ViewersApp()
    main_window.show()
    main_window.initialize()
    app.exec_()