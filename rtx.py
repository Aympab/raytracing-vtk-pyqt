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
    vtkTexture,
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
import numpy as np

model = "models/Nuclear_Power_Plant_v1/10078_Nuclear_Power_Plant_v1_L3.obj"
# scene = "models/naboo/naboo_complex.obj"

#TODO : changer la StartTheta ou StartPhi pour que la sphere sun pointe tjrs vers sont focal point ca serait insane
#TODO : add a comboBox with colors name to change diffuse color light

light_x = 0.0
light_y = 50.0
light_z = 50.0
sun_resolution = 6
sun_color = [1.0, 0.986, 0.24]
sun_ray_color = [1.0, 1.0, 0.24]
RayCastLength = 500.0

point_resolution = 5
intersect_color = [0.0, 0.0, 1.0] #blue
intersect_radius = 2.5

camera_focus = [0,0,0]

l2n = lambda l: np.array(l)
n2l = lambda n: list(n)

def calcVecR(vecInc, vecNor):
    vecInc = l2n(vecInc)
    vecNor = l2n(vecNor)
    
    vecRef = vecInc - 2*np.dot(vecInc, vecNor)*vecNor
    
    return n2l(vecRef)

#region superclass setup
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
        self.ui.rb_PreviewShadows.clicked.connect(self.vtk_widget.previewShadows)
        
        self.ui.cameraPos_x.valueChanged.connect(self.vtk_widget.cam_pos_x)
        self.ui.cameraPos_y.valueChanged.connect(self.vtk_widget.cam_pos_y)
        self.ui.cameraPos_z.valueChanged.connect(self.vtk_widget.cam_pos_z)
        
    def initialize(self):
        self.vtk_widget.start()
#endregion

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


        #################################
        ## POWERPLANT
        # powerplant_reader, powerplant_actor = modelFromFile(model)  
        # #the next lines do exactly what is in modelFromFile function but if we don't do this we cannot access stuff
        #################################
        powerplant_reader = readfile(model, 'obj')
        pp_mapper = vtkPolyDataMapper()
        pp_mapper.SetInputConnection(powerplant_reader.GetOutputPort())
        colors = vtkNamedColors()

        pp_actor = vtkActor()
        pp_actor.SetMapper(pp_mapper)
        pp_actor.GetProperty().SetColor(colors.GetColor3d('AliceBlue'))

        self.renderer.AddActor(pp_actor)
        self.powerplant_actor = pp_actor
        
        #################################
        ## LIGHT
        #################################
        self.light = vtk.vtkLight()
        self.light.SetIntensity(0.5)
        self.pos_Light = [light_x, light_y, light_z]
        self.light.SetPosition(self.pos_Light)
        self.light.SetDiffuseColor(1, 1, 1)
        self.light.SetFocalPoint(0.,0.,0.)
        # self.light.SetConeAngle(90)
        self.light.SetPositional(True)
        self.renderer.AddLight(self.light)
        self.followTarget = False #if the camera focal point is on 0,0,0 or on the target

        #################################
        ## sun_ball BALL TO SHOW WHERE IS LIGHT
        #################################
        sun_actor, self.sun_ball = addPoint(self.renderer, self.pos_Light, color=sun_color)
        self.sun_ball.SetPhiResolution(sun_resolution)
        self.sun_ball.SetThetaResolution(sun_resolution)
        # self.sun_ball.SetStartPhi(90) #to cut half a sphere
        # print(self.sun_ball.GetSt)
        sun_actor.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
        sun_actor.GetProperty().SetEdgeColor([0.,0.,0.])  
        self.sunOffset = 0.0


        #################################
        ##SUN's NORMALS
        # # Create a new 'vtkPolyDataNormals' and connect to the sun sphere
        #################################
        normalsCalcSun = vtk.vtkPolyDataNormals()
        normalsCalcSun.SetInputConnection(self.sun_ball.GetOutputPort())

        # Disable normal calculation at cell vertices
        normalsCalcSun.ComputePointNormalsOff()
        # Enable normal calculation at cell centers
        normalsCalcSun.ComputeCellNormalsOn()
        # Disable splitting of sharp edges
        normalsCalcSun.SplittingOff()
        # Disable global flipping of normal orientation
        normalsCalcSun.FlipNormalsOff()
        # Enable automatic determination of correct normal orientation
        normalsCalcSun.AutoOrientNormalsOn()
        # Perform calculation
        normalsCalcSun.Update()
        
        
        # Create a 'dummy' 'vtkCellCenters' to force the glyphs to the cell-centers
        dummy_cellCenterCalcSun = vtk.vtkCellCenters()
        dummy_cellCenterCalcSun.VertexCellsOn()
        dummy_cellCenterCalcSun.SetInputConnection(normalsCalcSun.GetOutputPort())

        # Create a new 'default' arrow to use as a glyph
        arrow = vtk.vtkArrowSource()

        # Create a new 'vtkGlyph3D'
        glyphSun = vtk.vtkGlyph3D()
        # Set its 'input' as the cell-center normals calculated at the sun's cells
        glyphSun.SetInputConnection(dummy_cellCenterCalcSun.GetOutputPort())
        # Set its 'source', i.e., the glyph object, as the 'arrow'
        glyphSun.SetSourceConnection(arrow.GetOutputPort())
        # Enforce usage of normals for orientation
        glyphSun.SetVectorModeToUseNormal()
        # Set scale for the arrow object
        glyphSun.SetScaleFactor(4)

        # Create a mapper for all the arrow-glyphs
        glyphMapperSun = vtk.vtkPolyDataMapper()
        glyphMapperSun.SetInputConnection(glyphSun.GetOutputPort())

        # Create an actor for the arrow-glyphs
        glyphActorSun = vtk.vtkActor()
        glyphActorSun.SetMapper(glyphMapperSun)
        glyphActorSun.GetProperty().SetColor(sun_color)
        # Add actor
        self.renderer.AddActor(glyphActorSun)

        #################################
        #Center point of cells of the sun
        #################################
        self.cellCenterSun = []

        self.cellCenterCalcSun = vtk.vtkCellCenters()
        self.cellCenterCalcSun.SetInputConnection(self.sun_ball.GetOutputPort())

        self.cellCenterCalcSun.Update()
        # Get the point centers from 'cellCenterCalc'
        pointsCellCentersSun = self.cellCenterCalcSun.GetOutput(0)
        for idx in range(pointsCellCentersSun.GetNumberOfPoints()):
            pos = pointsCellCentersSun.GetPoint(idx)
            _, point = addPoint(self.renderer, pos, radius=0.5, color=sun_color, resolution=10)
            # point.SetPhiResolution(1)
            # point.SetThetaResolution(1)
            self.cellCenterSun.append(point)


        #################################
        #Camera (source) object settings, not the actual vtk camera
        #################################
        self.pos_Camera = [100.0, 10.0, 30.0]
        _, self.cam_ball = addPoint(self.renderer, self.pos_Camera, color=[0.0, 1.0, 0.0])
        self.line_actor, self.line = addLine(self.renderer, camera_focus, self.pos_Camera, color=[1.,0.,0.])
        self.renderer.AddActor(self.line_actor) #this doesn't work with shadows

        #For the intersections
        self.obbTree = vtk.vtkOBBTree()
        self.obbTree.SetDataSet(powerplant_reader.GetOutput())
        self.obbTree.BuildLocator()



        #################################
        #RTX COMPUTING
        # #################################
        # Create a new 'vtkPolyDataNormals' and connect to our model
        normalsCalcModel = vtk.vtkPolyDataNormals()
        normalsCalcModel.SetInputConnection(powerplant_reader.GetOutputPort())
        
        # Disable normal calculation at cell vertices
        normalsCalcModel.ComputePointNormalsOff()
        # Enable normal calculation at cell centers
        normalsCalcModel.ComputeCellNormalsOn()
        # Disable splitting of sharp edges
        normalsCalcModel.SplittingOff()
        # Disable global flipping of normal orientation
        normalsCalcModel.FlipNormalsOff()
        # Enable automatic determination of correct normal orientation
        normalsCalcModel.AutoOrientNormalsOn()
        # Perform calculation
        normalsCalcModel.Update()


        self.lines_hit = []
        self.points_hit = []

        # Extract the normal-vector data at the sun's cells
        self.normalsSun = normalsCalcSun.GetOutput().GetCellData().GetNormals()
        # Extract the normal-vector data at the earth's cells
        self.normalsModel = normalsCalcModel.GetOutput().GetCellData().GetNormals()

        # Create a dummy 'vtkPoints' to act as a container for the point coordinates
        # where intersections are found
        dummy_points = vtk.vtkPoints()
        # Create a dummy 'vtkDoubleArray' to act as a container for the normal
        # vectors where intersections are found
        dummy_vectors = vtk.vtkDoubleArray()
        dummy_vectors.SetNumberOfComponents(3)
        # Create a dummy 'vtkPolyData' to store points and normals
        dummy_polydata = vtk.vtkPolyData()

        # Loop through all of sun's cell-centers
        for idx in range(pointsCellCentersSun.GetNumberOfPoints()):
            # Get coordinates of sun's cell center
            pointSun = pointsCellCentersSun.GetPoint(idx)
            # Get normal vector at that cell
            normalSun = self.normalsSun.GetTuple(idx)

            # Calculate the 'target' of the ray based on 'RayCastLength'
            pointRayTarget = n2l(l2n(pointSun) + RayCastLength*l2n(normalSun))
            
            # Check if there are any intersections for the given ray
            if isHit(self.obbTree, pointSun, pointRayTarget):
                # Retrieve coordinates of intersection points and intersected cell ids
                pointsInter, cellIdsInter = GetIntersect(self.obbTree, pointSun, pointRayTarget)
                # Get the normal vector at the earth cell that intersected with the ray
                normalModel = self.normalsModel.GetTuple(cellIdsInter[0])
                
                # Insert the coordinates of the intersection point in the dummy container
                dummy_points.InsertNextPoint(pointsInter[0])
                # Insert the normal vector of the intersection cell in the dummy container
                dummy_vectors.InsertNextTuple(normalModel)
                
                ac, lines = addLine(self.renderer, pointSun, pointsInter[0], color=sun_ray_color)
                
                # Render intersection points
                ac_point, point_hit = addPoint(self.renderer, pointsInter[0], radius=intersect_radius, color=[0.,0.,1.], resolution=point_resolution)

                #region display boucing ray DOESNT WORK
                # # Calculate the incident ray vector
                vecInc = n2l(l2n(pointRayTarget) - l2n(pointSun))
                # Calculate the reflected ray vector
                vecRef = calcVecR(vecInc, normalModel)
                
                # # Calculate the 'target' of the reflected ray based on 'RayCastLength'
                # pointRayReflectedTarget = n2l(l2n(pointsInter[0]) + RayCastLength*l2n(vecRef))

                # # Render lines/rays bouncing off earth with a 'ColorRayReflected' color
                # a, _ = addLine(self.renderer, pointsInter[0], pointRayReflectedTarget, [1,1,1])
                # self.renderer.AddActor(a)
            else:
                ac, lines = addLine(self.renderer, pointSun, pointRayTarget, color=sun_ray_color, opacity=0.25)
                ac_point, point_hit = addPoint(self.renderer, pointRayTarget, radius=intersect_radius, color=sun_ray_color, resolution=point_resolution)
                
            self.lines_hit.append((ac, lines))
            self.renderer.AddActor(ac)
            
            self.points_hit.append((ac_point, point_hit))

        #         #endregion

        # # Assign the dummy points to the dummy polydata
        # dummy_polydata.SetPoints(dummy_points)
        # # Assign the dummy vectors to the dummy polydata
        # dummy_polydata.GetPointData().SetNormals(dummy_vectors)
                
        # # Visualize normals as done previously but using 
        # # the 'dummyPolyData'
        # arrow = vtk.vtkArrowSource()

        # glyphEarth = vtk.vtkGlyph3D()
        # glyphEarth.SetInputData(dummy_polydata)
        # glyphEarth.SetSourceConnection(arrow.GetOutputPort())
        # glyphEarth.SetVectorModeToUseNormal()
        # glyphEarth.SetScaleFactor(5)

        # glyphMapperEarth = vtk.vtkPolyDataMapper()
        # glyphMapperEarth.SetInputConnection(glyphEarth.GetOutputPort())

        # glyphActorEarth = vtk.vtkActor()
        # glyphActorEarth.SetMapper(glyphMapperEarth)
        # glyphActorEarth.GetProperty().SetColor([0,0,1])

        # self.renderer.AddActor(glyphActorEarth)

        #################################
        #DISPLAY REBOUNCING RAYS
        #################################


        print("Number of lines : ", len(self.lines_hit))
        self.render_window.Render()
        self.intersect_list = []

#region methods
################################################################################
################################################################################
#                              CLASS METHODS                                   #
################################################################################
################################################################################
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
        self.render_window.Render()
        

    #intersections, moving cell centers, changing focal point of light
    def update_components(self):
        pointsVTKintersection = vtk.vtkPoints()
        # code = self.obbTree.IntersectWithLine(self.pos_Light, self.pos_Camera, pointsVTKintersection, None) #None for CellID but we will need this info later
        code = self.obbTree.IntersectWithLine(camera_focus, self.pos_Camera, pointsVTKintersection, None) #None for CellID but we will need this info later

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
                self.intersect_list.append(addPoint(self.renderer, p, radius=2.0, color=intersect_color))
                    
        else:
            # print("Same number of points")
            for (_, point), pos in zip(self.intersect_list, current_position_list) :
                point.SetCenter(pos)

        #if the light's focal point is following the camera position
        if self.followTarget : self.light.SetFocalPoint(self.pos_Camera)
        
        
        #Move the sun's center cell as well
        #Move the ray casting lines
        self.cellCenterCalcSun.Update()
        pointsCellCentersSun = self.cellCenterCalcSun.GetOutput(0)
        
        dummy_points = vtk.vtkPoints()
        dummy_vectors = vtk.vtkDoubleArray()
        dummy_vectors.SetNumberOfComponents(3)

        for idx, ((ac, line),
                  centerPoint,
                  (ac_pointHit, pointHit)) in enumerate(zip(self.lines_hit,
                                                                      self.cellCenterSun,
                                                                      self.points_hit)):
            pos = pointsCellCentersSun.GetPoint(idx)
            self.cellCenterSun[idx].SetCenter(pos)
            pointSun = pointsCellCentersSun.GetPoint(idx)
            normalSun = self.normalsSun.GetTuple(idx)
            
            pos = centerPoint.GetCenter()
            line.SetPoint1(pos)

            pointRayTarget = n2l(l2n(pointSun) + RayCastLength*l2n(normalSun))
            line.SetPoint2(pointRayTarget)

            
            if isHit(self.obbTree, line.GetPoint1(), line.GetPoint2()):
                #Change color
                ac.GetProperty().SetOpacity(1)
                
                pointsInter, cellIdsInter = GetIntersect(self.obbTree, pointSun, pointRayTarget)
                pointHit.SetCenter(pointsInter[0])
                ac_pointHit.GetProperty().SetColor(intersect_color)
            else:
                ac.GetProperty().SetOpacity(0.25)
                
                pointHit.SetCenter(pointRayTarget)
                ac_pointHit.GetProperty().SetColor(sun_ray_color)
                
                # pointsInter, cellIdsInter = GetIntersect(self.obbTree, pointSun, pointRayTarget)
                # normalModel = self.normalsModel.GetTuple(cellIdsInter[0])
                
                # dummy_points.InsertNextPoint(pointsInter[0])
                # dummy_vectors.InsertNextTuple(normalModel)
                
                # # hit_count += 1
                # ac, lines = addLine(self.renderer, pointSun, pointsInter[0], color=[0.0,0.0,1.0])
                # self.lines_hit.append((ac, lines))
                # self.renderer.AddActor(ac)

        

    def previewShadows(self, new_value):
        if new_value :
            # #we remove the line actor so we can display shadows
            self.renderer.RemoveActor(self.line_actor)
            
            for ((acLine, _), (acPoint, _)) in zip(self.lines_hit, self.points_hit):
                self.renderer.RemoveActor(acLine)
                self.renderer.RemoveActor(acPoint)

            # #we add an offset to the light pos or else we have
            # #the shadows of the sun's normals (arrows on the sphere)
            self.sunOffset = 10 

            self.renderer.UseShadowsOn()

        else :
            self.renderer.UseShadowsOff()
            self.renderer.AddActor(self.line_actor)
            self.sunOffset = 0.0
            
            for ((acLine, _), (acPoint, _)) in zip(self.lines_hit, self.points_hit):
                self.renderer.AddActor(acLine)
                self.renderer.AddActor(acPoint)


        #Rechange the position with the right offset
        x = self.light.GetPosition()[0]
        y = self.light.GetPosition()[1]
        z = self.light.GetPosition()[2]
        
        self.sun_ball.SetCenter(x, y, z+self.sunOffset)
        self.render_window.Render()
#endregion

#region Light
################################################################################
################################################################################
#                            LIGHT INTERACTION                                 #
################################################################################
################################################################################
    def light_pos_x(self, new_value):
        y = self.light.GetPosition()[1]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(new_value, y, z)
        self.sun_ball.SetCenter(new_value, y, z+self.sunOffset)
        
        self.pos_Light = [new_value, y, z]
        # self.line.SetPoint1(self.pos_Light)

        self.update_components()

        self.render_window.Render()
        
    def light_pos_y(self, new_value):
        x = self.light.GetPosition()[0]
        z = self.light.GetPosition()[2]
        
        self.light.SetPosition(x, new_value, z)
        self.sun_ball.SetCenter(x, new_value, z+self.sunOffset)
        
        self.pos_Light = [x, new_value, z]
        # self.line.SetPoint1(self.pos_Light)

        self.update_components()

        self.render_window.Render()

    def light_pos_z(self, new_value):
        x = self.light.GetPosition()[0]
        y = self.light.GetPosition()[1]

        self.light.SetPosition(x, y, new_value)
        self.sun_ball.SetCenter(x, y, new_value+self.sunOffset)

        self.pos_Light = [x, y, new_value]
        # self.line.SetPoint1(self.pos_Light)

        self.update_components()

        self.render_window.Render()

    def light_intensity(self, new_value):
        self.light.SetIntensity(new_value/100.)
        self.render_window.Render()

    def light_coneAngle(self, new_value):
        self.light.SetConeAngle(new_value)
        
        if(new_value < 20):
            self.sun_ball.SetPhiResolution(new_value)
            self.sun_ball.SetThetaResolution(new_value)
        else :
            self.sun_ball.SetPhiResolution(sun_resolution)
            self.sun_ball.SetThetaResolution(sun_resolution)

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
#endregion

#region Camera
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

        self.update_components()

        self.render_window.Render()
        
    def cam_pos_y(self, new_value):
        x = self.cam_ball.GetCenter()[0]
        z = self.cam_ball.GetCenter()[2]
        
        self.cam_ball.SetCenter(x, new_value, z)
        
        self.pos_Camera = [x, new_value, z]
        self.line.SetPoint2(self.pos_Camera)

        self.update_components()

        self.render_window.Render()

    def cam_pos_z(self, new_value):
        x = self.cam_ball.GetCenter()[0]
        y = self.cam_ball.GetCenter()[1]

        self.cam_ball.SetCenter(x, y, new_value)

        self.pos_Camera = [x, y, new_value]
        self.line.SetPoint2(self.pos_Camera)

        self.update_components()

        self.render_window.Render()
#endregion

    #END OF MAIN class QMeshViewer
    ##############################

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