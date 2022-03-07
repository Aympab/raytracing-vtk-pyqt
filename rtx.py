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


#TODO : Rename pos_Light en pLight
#TODO : AddPoint en AddSphere

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


        ## POWERPLANT
        # powerplant_reader, powerplant_actor = modelFromFile(model)  
        # #the next lines do exactly what is in modelFromFile function but if we don't do this we cannot access stuff
        powerplant_reader = readfile(model, 'obj')
        pp_mapper = vtkPolyDataMapper()
        pp_mapper.SetInputConnection(powerplant_reader.GetOutputPort())
        colors = vtkNamedColors()

        pp_actor = vtkActor()
        pp_actor.SetMapper(pp_mapper)
        pp_actor.GetProperty().SetColor(colors.GetColor3d('AliceBlue'))

        renderer.AddActor(pp_actor)
        self.powerplant_actor = pp_actor

        ## LIGHT
        self.light = vtk.vtkLight()
        self.light.SetIntensity(0.5)
        self.light.SetPosition(light_x, light_y, light_z)
        # self.light.SetLightType(2)
        self.light.SetDiffuseColor(1, 1, 1)
        renderer.AddLight(self.light)
        
        ## sun_ball BALL TO SHOW WHERE IS LIGHT
        self.pos_Light = [light_x, light_y, light_z]
        _, self.sun_ball = addPoint(renderer, self.pos_Light, color=[1.0, 1.0, 0.0])

        self.render_window = render_window
        self.interactor = interactor
        self.renderer = renderer
        
        self.pos_Camera = [100.0, 10.0, 30.0]
        _, self.cam_ball = addPoint(renderer, self.pos_Camera, color=[0.0, 1.0, 0.0])
        self.line = addLine(renderer, self.pos_Light, self.pos_Camera)


        self.obbTree = vtk.vtkOBBTree()
        self.obbTree.SetDataSet(powerplant_reader.GetOutput())
        self.obbTree.BuildLocator()
        
        
        self.intersect_list = []

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
        # self.light.SetIntensity(new_value)
        
        self.render_window.Render()

    def intersect(self):

        pointsVTKintersection = vtk.vtkPoints()
        code = self.obbTree.IntersectWithLine(self.pos_Light, self.pos_Camera, pointsVTKintersection, None) #None for CellID but we will need this info later

        pointsVTKIntersectionData = pointsVTKintersection.GetData()
        noPointsVTKIntersection = pointsVTKIntersectionData.GetNumberOfTuples()
        
        # self.intersect_list = []
        current_position_list = []
        
        for idx in range(noPointsVTKIntersection):
            _tup = pointsVTKIntersectionData.GetTuple3(idx)
            current_position_list.append(_tup)
            
        if(noPointsVTKIntersection != len(self.intersect_list)):
            if(noPointsVTKIntersection < len(self.intersect_list)):
                for (a, _) in self.intersect_list :
                    self.renderer.RemoveActor(a)
                self.intersect_list.clear() #we clear the array

            for p in current_position_list:
                self.intersect_list.append(addPoint(self.renderer, p, radius=2.0, color=[0.0, 0.0, 1.0]))
                    
        else:
            # print("Same number of points")
            for (_, point), pos in zip(self.intersect_list, current_position_list) :
                point.SetCenter(pos)
        




    def light_pos_x(self, new_value):
        y = self.light.GetPosition()[1]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(new_value, y, z)
        self.sun_ball.SetCenter(new_value, y, z)
        
        self.pos_Light = [new_value, y, z]
        self.line.SetPoint1(self.pos_Light)
        # addLine(self.renderer, self.pos_Light, self.pos_Camera)

        self.intersect()

        self.render_window.Render()
        
        
    def light_pos_y(self, new_value):
        x = self.light.GetPosition()[0]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(x, new_value, z)
        self.sun_ball.SetCenter(x, new_value, z)
        
        self.pos_Light = [x, new_value, z]
        self.line.SetPoint1(self.pos_Light)
        # addLine(self.renderer, self.pos_Light, self.pos_Camera)

        self.intersect()

        self.render_window.Render()

    def light_pos_z(self, new_value):
        x = self.light.GetPosition()[0]
        y = self.light.GetPosition()[1]

        self.light.SetPosition(x, y, new_value)
        self.sun_ball.SetCenter(x, y, new_value)

        self.pos_Light = [x, y, new_value]
        self.line.SetPoint1(self.pos_Light)
        # addLine(self.renderer, self.pos_Light, self.pos_Camera)

        self.intersect()

        self.render_window.Render()
        
    def light_intensity(self, new_value):
        self.light.SetIntensity(new_value/100.)
        self.render_window.Render()


    def save_event(self):
        print(self.light.GetFocalPoint())
        # self.light.SetFocalPoint((100,100,100))
        
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