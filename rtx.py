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
    vtkCamera,
    vtkTexture
)
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtk import vtkPNGReader, vtkJPEGReader, vtkTextureMapToSphere
from utils import *
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter

model = "models/Nuclear_Power_Plant_v1/10078_Nuclear_Power_Plant_v1_L3.obj"
# scene = "models/naboo/naboo_complex.obj"


light_x = 0.0
light_y = 50.0
light_z = 50.0

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
        
        colors = vtk.vtkNamedColors()

        renderer = vtk.vtkRenderer()
        render_window = interactor.GetRenderWindow()
        render_window.AddRenderer(renderer)
        interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        render_window.SetInteractor(interactor)
        # render_window.SetSize(512, 512)
        interactor.SetRenderWindow(render_window)
        renderer.SetBackground(colors.GetColor3d("DarkGreen"))
        # renderer.SetBackground(colors.GetColor3d("AliceBlue"))

        # Set up a nice camera position.
        # camera = vtkCamera()
        # camera.SetPosition(100, -21.0, 30.8)
        # camera.SetFocalPoint(0.0, 0.0, 0.0)
        # camera.SetClippingRange(3.2, 10.2)
        # camera.SetViewUp(0.3, 1.0, 0.13)
        # renderer.SetActiveCamera(camera)

        transform = vtkTransform()
        transform.Translate(1.0, 0.0, 0.0)


        
        # renderer.AddActor(axes)
        #renderer.AddActor(actor)
        # renderer.AddActor(naboo_actor)

        ## POWERPLANT
        powerplant_reader, powerplant_actor = modelFromFile(model)
        renderer.AddActor(powerplant_actor)
        self.powerplant_actor = powerplant_actor


        ## LIGHT
        self.light1 = vtk.vtkLight()
        self.light1.SetIntensity(0.5)
        self.light1.SetPosition(light_x, light_y, light_z)
        self.light1.SetLightType(2)
        self.light1.SetDiffuseColor(1, 1, 1)
        renderer.AddLight(self.light1)
        
        ## SUN BALL TO SHOW WHERE IS LIGHT
        self.pSource = [light_x, light_y, light_z]
        self.sun = addPoint(renderer, self.pSource, color=[1.0, 1.0, 0.0])

        self.render_window = render_window
        self.interactor = interactor
        self.renderer = renderer

        self.pTarget = [10.0, 0.0, 10.0]
        
        self.cam = addPoint(renderer, self.pTarget, color=[0.0, 1.0, 0.0])
        self.line = addLine(renderer, self.pSource, self.pTarget)
        # addLine(renderer, self.pSource, self.pTarget)
        # vtk_show(renderer)
        
        self.renderer = renderer

    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    def Switch_Mode(self, new_value):
        # self.actor.GetProperty().SetRepresentation(new_value)
        self.powerplant_actor.GetProperty().SetRepresentation(new_value)
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

        self.powerplant_actor.SetTexture(texture)


    def set_Resolution(self, new_value):
        # self.sphere.SetPhiResolution(new_value)
        # self.sphere.SetThetaResolution(new_value)
        
        # self.power_plant.SetPosition(new_value, new_value, new_value)
        # self.light1.SetIntensity(new_value)
        
        self.render_window.Render()

    def light_pos_x(self, new_value):
        y = self.light1.GetPosition()[1]
        z = self.light1.GetPosition()[2]
        
        self.light1.SetPosition(new_value, y, z)
        self.sun.SetCenter(new_value, y, z)
        
        self.pSource = [new_value, y, z]
        self.line.SetPoint1(self.pSource)
        # addLine(self.renderer, self.pSource, self.pTarget)

        self.render_window.Render()
        
        
    def light_pos_y(self, new_value):
        x = self.light1.GetPosition()[0]
        z = self.light1.GetPosition()[2]
        
        self.light1.SetPosition(x, new_value, z)
        self.sun.SetCenter(x, new_value, z)
        
        self.pSource = [x, new_value, z]
        self.line.SetPoint1(self.pSource)
        # addLine(self.renderer, self.pSource, self.pTarget)
        
        self.render_window.Render()
        
    def light_pos_z(self, new_value):
        x = self.light1.GetPosition()[0]
        y = self.light1.GetPosition()[1]
        
        self.light1.SetPosition(x, y, new_value)
        self.sun.SetCenter(x, y, new_value)
        
        self.pSource = [x, y, new_value]
        self.line.SetPoint1(self.pSource)
        # addLine(self.renderer, self.pSource, self.pTarget)
        
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