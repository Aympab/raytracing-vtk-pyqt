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
from vtkmodules.vtkRenderingOpenGL2 import (
    vtkCameraPass,
    vtkRenderPassCollection,
    vtkSequencePass,
    vtkShadowMapPass
)
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtk import vtkPNGReader, vtkJPEGReader, vtkTextureMapToSphere
from utils import *
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter

model = "models/Nuclear_Power_Plant_v1/10078_Nuclear_Power_Plant_v1_L3.obj"
# scene = "models/naboo/naboo_complex.obj"

#TODO : changer la StartTheta ou StartPhi pour que la sphere sun pointe tjrs vers sont focal point ca serait insane

light_x = 0.0
light_y = 50.0
light_z = 50.0
sun_resolution = 6

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
        self.ui.radioButton.clicked.connect(self.vtk_widget.button_event)
        self.ui.saveButton.clicked.connect(self.vtk_widget.light_source) # change save_button to light_source_button
        
        self.ui.lightIntensity.valueChanged.connect(self.vtk_widget.light_intensity)
        self.ui.lightPos_x.valueChanged.connect(self.vtk_widget.light_pos_x)
        self.ui.lightPos_y.valueChanged.connect(self.vtk_widget.light_pos_y)
        self.ui.lightPos_z.valueChanged.connect(self.vtk_widget.light_pos_z)
        self.ui.light_coneAngle.valueChanged.connect(self.vtk_widget.light_coneAngle)
        self.ui.light_focalPoint.clicked.connect(self.vtk_widget.light_focalPointFollow)
        self.ui.light_focalPoint_button.clicked.connect(self.vtk_widget.light_focalPoint)
        
        self.ui.cameraPos_x.valueChanged.connect(self.vtk_widget.cam_pos_x)
        self.ui.cameraPos_y.valueChanged.connect(self.vtk_widget.cam_pos_y)
        self.ui.cameraPos_z.valueChanged.connect(self.vtk_widget.cam_pos_z)
        
    def initialize(self):
        self.vtk_widget.start()

class QMeshViewer(QtWidgets.QFrame):
    def __init__(self, parent):
        super(QMeshViewer, self).__init__(parent)
        
        self.interactor = QVTKRenderWindowInteractor(self)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        
        colors = vtk.vtkNamedColors()

        self.renderer = vtk.vtkRenderer()
        self.render_window = self.interactor.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.render_window.SetInteractor(self.interactor)
        # render_window.SetSize(512, 512)
        self.interactor.SetRenderWindow(self.render_window)
        self.renderer.SetBackground(colors.GetColor3d("DarkGreen"))
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

        self.renderer.AddActor(pp_actor)
        self.powerplant_actor = pp_actor

        ## LIGHT
        self.light = vtk.vtkLight()
        self.light.SetIntensity(0.5)
        self.light.SetPosition(light_x, light_y, light_z)
        # self.light.SetLightType(2)
        self.light.SetDiffuseColor(1, 1, 1)
        self.light.SetFocalPoint(0.,0.,0.)
        # self.light.SetConeAngle(90)
        # print(self.light.GetConeAngle())
        self.light.SetPositional(True)
        self.renderer.AddLight(self.light)
        self.followTarget = False #if the camera focal point is on 0,0,0 or on the target


        ## sun_ball BALL TO SHOW WHERE IS LIGHT
        self.pos_Light = [light_x, light_y, light_z]
        sun_actor, self.sun_ball = addPoint(self.renderer, self.pos_Light, color=[1.0, 1.0, 0.0])
        self.sun_ball.SetPhiResolution(sun_resolution)
        self.sun_ball.SetThetaResolution(sun_resolution)
        self.sun_ball.SetStartPhi(90) #to cut half a sphere
        sun_actor.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
        sun_actor.GetProperty().SetEdgeColor([0.,0.,0.])  
        
        self.pos_Camera = [100.0, 10.0, 30.0]
        _, self.cam_ball = addPoint(self.renderer, self.pos_Camera, color=[0.0, 1.0, 0.0])
        self.line = addLine(self.renderer, self.pos_Light, self.pos_Camera)


        self.obbTree = vtk.vtkOBBTree()
        self.obbTree.SetDataSet(powerplant_reader.GetOutput())
        self.obbTree.BuildLocator()

        self.intersect_list = []


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

        #if the light's focal point is following the camera position
        if self.followTarget : self.light.SetFocalPoint(self.pos_Camera)


################################################################################
################################################################################
#                            LIGHT INTERACTION                                 #
################################################################################
################################################################################
    def light_pos_x(self, new_value):
        y = self.light.GetPosition()[1]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(new_value, y, z)
        self.sun_ball.SetCenter(new_value, y, z)
        
        self.pos_Light = [new_value, y, z]
        self.line.SetPoint1(self.pos_Light)

        self.intersect()

        self.render_window.Render()
        
    def light_pos_y(self, new_value):
        x = self.light.GetPosition()[0]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(x, new_value, z)
        self.sun_ball.SetCenter(x, new_value, z)
        
        self.pos_Light = [x, new_value, z]
        self.line.SetPoint1(self.pos_Light)

        self.intersect()

        self.render_window.Render()

    def light_pos_z(self, new_value):
        x = self.light.GetPosition()[0]
        y = self.light.GetPosition()[1]

        self.light.SetPosition(x, y, new_value)
        self.sun_ball.SetCenter(x, y, new_value)

        self.pos_Light = [x, y, new_value]
        self.line.SetPoint1(self.pos_Light)

        self.intersect()

        self.render_window.Render()

    def light_intensity(self, new_value):
        self.light.SetIntensity(new_value/100.)
        self.render_window.Render()

    def light_coneAngle(self, new_value):
        self.light.SetConeAngle(new_value)
        self.render_window.Render()

    def light_focalPoint(self, new_value):
        self.light.SetFocalPoint(self.pos_Camera)
        self.render_window.Render()

    def light_focalPointFollow(self, new_value):
        # print("Follow target = ", followTarget)
        if new_value:
            self.light.SetFocalPoint(self.pos_Camera)
        else:
            self.light.SetFocalPoint(0.,0.,0.)

        self.followTarget = not self.followTarget
        
        self.render_window.Render()

    def light_source(self):
        if(self.light.GetLightType() == 3):
            self.light.SetLightType(2)
            self.light.SetConeAngle(91)
            print("Light from camera. Click again to change")
        else:
            self.light.SetLightType(3)
            print("Light from sun. Click again to change")

        self.render_window.Render()

################################################################################
################################################################################
#                            CAMERA INTERACTION                                #
################################################################################
################################################################################
    def cam_pos_x(self, new_value):
        y = self.cam_ball.GetCenter()[1]
        z = self.cam_ball.GetCenter()[2]

        self.cam_ball.SetCenter(new_value, y, z)

        self.pos_Camera = [new_value, y, z]
        self.line.SetPoint2(self.pos_Camera)

        self.intersect()

        self.render_window.Render()
        
    def cam_pos_y(self, new_value):
        x = self.cam_ball.GetCenter()[0]
        z = self.cam_ball.GetCenter()[2]
        
        self.cam_ball.SetCenter(x, new_value, z)
        
        self.pos_Camera = [x, new_value, z]
        self.line.SetPoint2(self.pos_Camera)

        self.intersect()

        self.render_window.Render()

    def cam_pos_z(self, new_value):
        x = self.cam_ball.GetCenter()[0]
        y = self.cam_ball.GetCenter()[1]

        self.cam_ball.SetCenter(x, y, new_value)

        self.pos_Camera = [x, y, new_value]
        self.line.SetPoint2(self.pos_Camera)

        self.intersect()

        self.render_window.Render()

    #END OF MAIN class QMeshViewer

################################################################################
################################################################################
#                                       MAIN                                   #
################################################################################
################################################################################
if __name__ == "__main__":
    with open("Mini_app_Qt_VTK.ui") as ui_file:
        with open("Mini_app_Qt_VTK.py", "w") as py_ui_file:
            uic.compileUi(ui_file, py_ui_file)

    app = QtWidgets.QApplication(["Application-RTX"])
    main_window = ViewersApp()
    main_window.show()
    main_window.initialize()
    app.exec_()