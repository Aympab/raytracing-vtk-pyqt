from asyncore import poll3
from cmath import sin, tan
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import uic, QtWidgets
from readVTP import *
# from rich.progress import Progress
from tqdm import tqdm
import matplotlib.pyplot as plt
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkTexture,
)
from vtk import vtkJPEGReader
from utils import *
import numpy as np

model = "models/Nuclear_Power_Plant_v1/10078_Nuclear_Power_Plant_v1_L3.obj"
# scene = "models/naboo/naboo_complex.obj"

#TODO : changer la StartTheta ou StartPhi pour que la sphere sun pointe tjrs vers sont focal point ca serait insane
#TODO : add a comboBox with colors name to change diffuse color light

light_x = 0.0
light_y = 50.0
light_z = 200.0
sun_resolution = 4
sun_color = [1.0, 0.986, 0.24]
sun_ray_color = [1.0, 1.0, 0.24]
RayCastLength = 1000.0

point_resolution = 5
intersect_color = [0.0, 0.0, 1.0] #blue
intersect_radius = 2.5

camera_focus = [0,0,0]



#region Superclass and UI setup
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
        
        self.ui.button_RTX.clicked.connect(self.vtk_widget.compute_RTX)
        self.ui.width.valueChanged.connect(self.vtk_widget.change_width)
        self.ui.height.valueChanged.connect(self.vtk_widget.change_height)
        self.ui.spinBox_maxDepth.valueChanged.connect(self.vtk_widget.change_maxDepth)
        
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

        self.renderer.GetActiveCamera().SetPosition(0,0,500)


        #################################
        ## POWERPLANT
        #################################
        powerplant_reader = readfile(model, 'obj')
        pp_mapper = vtkPolyDataMapper()
        pp_mapper.SetInputConnection(powerplant_reader.GetOutputPort())
        colors = vtkNamedColors()

        pp_actor = vtkActor()
        pp_actor.SetMapper(pp_mapper)
        pp_actor.GetProperty().SetColor(colors.GetColor3d('Coral'))

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
        self.light.SetAmbientColor(1.,1.,1.)
        self.light.SetSpecularColor(1.,1.,1.)
        self.light.SetFocalPoint(0.,0.,0.)
        # self.light.SetConeAngle(90)
        self.light.SetPositional(True)
        self.renderer.AddLight(self.light)
        
        
        
        #if the camera focal point is on 0,0,0 or on the target :
        self.followTarget = False 

        #################################
        #################################
        #Camera (source) settings, not the actual vtk camera
        #################################
        #################################
        self.pos_Camera = [100.0, 10.0, 30.0]
        _, self.cam_ball = addPoint(self.renderer, self.pos_Camera, color=[0.0, 1.0, 0.0])
        self.line_actor, self.line = addLine(self.renderer, camera_focus, self.pos_Camera, color=[1.,0.,0.])
        self.renderer.AddActor(self.line_actor) #this doesn't work with shadows


        #################################
        ## sun_ball BALL TO LIVE-raytrace
        #################################
        self.sun_actor, self.sun_ball = addPoint(self.renderer, self.pos_Light, color=sun_color)
        self.sun_ball.SetPhiResolution(sun_resolution)
        self.sun_ball.SetThetaResolution(sun_resolution)
        self.sun_ball.SetStartPhi(90) #to cut half a sphere
        self.sun_actor.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
        self.sun_actor.GetProperty().SetEdgeColor([0.,0.,0.])  
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
        self.glyphActorSun = vtk.vtkActor()
        self.glyphActorSun.SetMapper(glyphMapperSun)
        self.glyphActorSun.GetProperty().SetColor(sun_color)
        # Add actor
        self.renderer.AddActor(self.glyphActorSun)

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

        #For the intersections
        self.obbTree = vtk.vtkOBBTree()
        self.obbTree.SetDataSet(powerplant_reader.GetOutput())
        self.obbTree.BuildLocator()



        #################################
        #LIVE RTX COMPUTING
        # #################################
        # Create a new 'vtkPolyDataNormals' and connect to our model
        normalsCalcModel = vtk.vtkPolyDataNormals()
        normalsCalcModel.SetInputConnection(powerplant_reader.GetOutputPort())
        normalsCalcModel.ComputePointNormalsOff()
        normalsCalcModel.ComputeCellNormalsOn()
        normalsCalcModel.SplittingOff()
        normalsCalcModel.FlipNormalsOff()
        normalsCalcModel.AutoOrientNormalsOn()
        normalsCalcModel.Update()

        # Create a dummy 'vtkPoints' to act as a container for the point coordinates
        # where intersections are found
        self.dummy_points = vtk.vtkPoints()
        # Create a dummy 'vtkDoubleArray' to act as a container for the normal
        # vectors where intersections are found
        self.dummy_vectors = vtk.vtkDoubleArray()
        self.dummy_vectors.SetNumberOfComponents(3)
        # Create a dummy 'vtkPolyData' to store points and normals
        self.dummy_polydata = vtk.vtkPolyData()
        
        
        self.lines_hit = []
        self.points_hit = []
        self.lines_bounce = []

        # Extract the normal-vector data at the sun's cells
        self.normalsSun = normalsCalcSun.GetOutput().GetCellData().GetNormals()
        # Extract the normal-vector data at the model's cells
        self.normalsModel = normalsCalcModel.GetOutput().GetCellData().GetNormals()

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
                normalModel =  self.normalsModel.GetTuple(cellIdsInter[0])
                # Insert the coordinates of the intersection point in the dummy container
                self.dummy_points.InsertNextPoint(pointsInter[0])
                
                directionRay = normalize(n2l(l2n(self.pos_Camera) - l2n(pointsInter[0])))
                
                # Insert the normal vector of the intersection cell in the dummy container
                self.dummy_vectors.InsertNextTuple(directionRay)

                ac, line = addLine(self.renderer, pointSun, pointsInter[0], color=sun_ray_color)
                # Render intersection points
                ac_point, point_hit = addPoint(self.renderer, pointsInter[0], radius=intersect_radius, color=[0.,0.,1.], resolution=point_resolution)

            else:
                ac, line = addLine(self.renderer, pointSun, pointRayTarget, color=sun_ray_color, opacity=0.25)
                ac_point, point_hit = addPoint(self.renderer, pointRayTarget, radius=intersect_radius, color=sun_ray_color, resolution=point_resolution)

            self.lines_hit.append((ac, line))
            self.renderer.AddActor(ac)
            

            self.points_hit.append((ac_point, point_hit))

        # Assign the dummy points to the dummy polydata
        self.dummy_polydata.SetPoints(self.dummy_points)
        # Assign the dummy vectors to the dummy polydata
        self.dummy_polydata.GetPointData().SetNormals(self.dummy_vectors)
                
        # Visualize normals as done previously but using 
        # the 'dummyPolyData'
        self.glyphModel = vtk.vtkGlyph3D()
        self.glyphModel.SetInputData(self.dummy_polydata)
        self.glyphModel.SetSourceConnection(arrow.GetOutputPort())
        self.glyphModel.SetVectorModeToUseNormal()
        self.glyphModel.SetScaleFactor(20)

        self.glyphMapperModel = vtk.vtkPolyDataMapper()
        self.glyphMapperModel.SetInputConnection(self.glyphModel.GetOutputPort())

        self.glyphActorModel = vtk.vtkActor()
        self.glyphActorModel.SetMapper(self.glyphMapperModel)
        self.glyphActorModel.GetProperty().SetColor(intersect_color)

        self.renderer.AddActor(self.glyphActorModel)

        #endregion


        #################################
        #PLANE (screen simulation)
        #################################
        x,y,z,normal = self.compute_plane_pos()
        self.pointsScreen = []
        self.pointsScreen.append(addPoint(self.renderer, (x, y+10, z+10), radius=0.001, resolution=1))
        self.pointsScreen.append(addPoint(self.renderer, (x, y-10, z+10), radius=0.001, resolution=1))
        self.pointsScreen.append(addPoint(self.renderer, (x, y+10, z-10), radius=0.001, resolution=1))
        # self.pointsScreen.append(addPoint(self.renderer, (x, y-ratio, z-ratio), radius=0.001, resolution=1))

        p = [point[1].GetCenter() for point in self.pointsScreen]
        
        plane_source = vtk.vtkPlaneSource()
        plane_source.SetOrigin(p[0])
        plane_source.SetPoint1(p[1])
        plane_source.SetPoint2(p[2])
        plane_source.SetNormal(normal)
        plane_source.SetResolution(4, 8)
        # plane_source.SetRepresentation(1)
        plane_source.Update()

        plane_mapper = vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane_source.GetOutputPort())
        plane_actor = vtkActor()
        plane_actor.SetMapper(plane_mapper)
        plane_actor.GetProperty().SetColor([0,0,0])
        plane_actor.GetProperty().SetRepresentationToWireframe()

        self.renderer.AddActor(plane_actor)
        self.screen_plane = (plane_actor, plane_source)

        print(f"Sun resolution : {sun_resolution}\nNumber of rays (live rendering) from the sun : {len(self.lines_hit)}")
        self.render_window.Render()
        self.intersect_list = []
        self.pic_width = 4
        self.pic_height = 2
        self.maxDepth = 3

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

        self.dummy_points.Reset()
        self.dummy_vectors.Reset()

        #Move the sun's center cell as well
        #Move the ray casting lines
        self.cellCenterCalcSun.Update()
        pointsCellCentersSun = self.cellCenterCalcSun.GetOutput(0)
        
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

            
            if isHit(self.obbTree, line.GetPoint1(), pointRayTarget):
                
                #Change color
                ac.GetProperty().SetOpacity(1)
                
                pointsInter, cellIdsInter = GetIntersect(self.obbTree, pointSun, pointRayTarget)
                ac_pointHit.GetProperty().SetColor(intersect_color)
                
                normalModel = self.normalsModel.GetTuple(idx)
                # print(pointsInter[0])
                
                if(len(pointsInter) > 0):
                    pointHit.SetCenter(pointsInter[0])
                    self.dummy_points.InsertNextPoint(pointsInter[0])
                    line.SetPoint2(pointsInter[0])
                
                #normale en direction de la pos caméra
                self.dummy_vectors.InsertNextTuple(n2l(l2n(self.pos_Camera)-l2n(pointsInter[0])))
                
                
            else:
                line.SetPoint2(pointRayTarget)
                
                ac.GetProperty().SetOpacity(0.25)
                
                pointHit.SetCenter(pointRayTarget)
                ac_pointHit.GetProperty().SetColor(sun_ray_color)

        # Assign the dummy points to the dummy polydata
        self.dummy_polydata.SetPoints(self.dummy_points)
        # Assign the dummy vectors to the dummy polydata
        self.dummy_polydata.GetPointData().SetNormals(self.dummy_vectors)
        
        arrow = vtk.vtkArrowSource()
        self.glyphModel.SetInputData(self.dummy_polydata)
        self.glyphModel.SetSourceConnection(arrow.GetOutputPort())
        # self.glyphModel.SetVectorModeToUseNormal()
        
        self.glyphMapperModel.SetInputConnection(self.glyphModel.GetOutputPort())
        # self.glyphActorModel.SetMapper(glyphMapperModel)
        
        #Update screen position
        x,y,z,normal = self.compute_plane_pos()
        
        self.pointsScreen[0][1].SetCenter((x, y+10, z+10))
        self.pointsScreen[1][1].SetCenter((x, y-10, z+10))
        self.pointsScreen[2][1].SetCenter((x, y+10, z-10))
        
        p = [point[1].GetCenter() for point in self.pointsScreen]
        
        self.screen_plane[1].SetOrigin(p[0])
        self.screen_plane[1].SetPoint1(p[1])
        self.screen_plane[1].SetPoint2(p[2])
        self.screen_plane[1].SetNormal(normal)

        #END update_components
        ######################

    def previewShadows(self, new_value):
        if new_value :
            self.setActorsForRendering(False)
            # #we add an offset to the light pos or else we have
            # #the shadows of the sun's normals (arrows on the sphere)
            self.sunOffset = 10 
            self.renderer.UseShadowsOn()

        else :
            self.setActorsForRendering(True)
            self.renderer.UseShadowsOff()


        x = self.light.GetPosition()[0]
        y = self.light.GetPosition()[1]
        z = self.light.GetPosition()[2]
        
        self.light.SetConeAngle(40)

        #Rechange the position with the right offset
        self.sun_ball.SetCenter(x, y, z+self.sunOffset)
        self.render_window.Render()
        
        
    def setActorsForRendering(self, add):
        if not add :
            self.renderer.RemoveActor(self.sun_actor)
            self.renderer.RemoveActor(self.glyphActorSun)
            # self.renderer.RemoveActor(self.cam_ball)
            self.renderer.RemoveActor(self.line_actor)
            
            for ((acLine, _), (acPoint, _)) in zip(self.lines_hit, self.points_hit):
                self.renderer.RemoveActor(acLine)
                self.renderer.RemoveActor(acPoint)

            self.renderer.RemoveActor(self.glyphActorModel)
            self.renderer.RemoveActor(self.glyphActorSun)
        else:
            self.renderer.AddActor(self.line_actor)
            self.sunOffset = 0.0
            for ((acLine, _), (acPoint, _)) in zip(self.lines_hit, self.points_hit):
                self.renderer.AddActor(acLine)
                self.renderer.AddActor(acPoint)

            self.renderer.AddActor(self.glyphActorModel)
            self.renderer.AddActor(self.glyphActorSun)
            # self.renderer.RemoveActor(self.cam_ball)
            self.renderer.AddActor(self.sun_actor)
            self.renderer.AddActor(self.glyphActorSun)
        
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
        
    def compute_plane_pos(self):
        centre = self.pos_Camera
        (x, y, z) = centre #+ quelquechose
        
        normal = (camera_focus[0]-x, camera_focus[1]-y, camera_focus[2]-x)
        normal = normal / np.linalg.norm(normal)

        weight, height = 30, 10

        offset = 20
        x += normal[0] * offset
        y += normal[1] * offset
        z += normal[2] * offset
        
        return x, y ,z, normal

    def change_width(self, new_value):
        self.pic_width = new_value

    def change_height(self, new_value):
        self.pic_height = new_value

    def change_maxDepth(self, new_value):
        self.maxDepth = new_value

    def compute_RTX(self):
        max_depth = self.maxDepth
        #remove sphere to avoid ray castings on it
        self.renderer.RemoveActor(self.sun_actor)
        self.renderer.RemoveActor(self.glyphActorSun)
        # self.renderer.RemoveActor(self.cam_ball)
        self.render_window.Render()
        
        cam = self.renderer.GetActiveCamera()
        originPos = cam.GetPosition()
        focal = cam.GetFocalPoint()
        clipping = cam.GetClippingRange()
        viewup = cam.GetViewUp()
        
        height = self.pic_height
        width = self.pic_width
        ratio = float(width) / height
        
        screen = (-1, 1 / ratio, 1, -1 / ratio)
        
        image = np.zeros((height, width, 3))

        print(f"Computing raytracing of {height} * {width} image and max depth {max_depth}")

        #Get the transform 
        inv = vtk.vtkMatrix4x4()
        
        cam.GetModelViewTransformMatrix().Invert(cam.GetModelViewTransformMatrix(), inv)
        tr_mat = np.zeros((4,4))
        for i in range(4) :
            for j in range(4) :
                tr_mat[i, j] = inv.GetElement(i,j)

        top = np.array([0, screen[1], 0, 1])#.reshape(-1,1)
        bottom = np.array([0, screen[3], 0, 1])#.reshape(-1,1)
        left = np.array([screen[0], 0, 0, 1])#.reshape(-1,1)
        right = np.array([screen[2], 0, 0, 1])#.reshape(-1,1)

        top = tr_mat@top
        bottom = tr_mat@bottom
        left = tr_mat@left
        right = tr_mat@right
        
        cam_pos = np.array([0,0,2,1])#.reshape(-1,1)
        cam_pos = tr_mat@cam_pos
        cam_pos = (cam_pos[0], cam_pos[1], cam_pos[2])
        # self.pos_Camera = cam_pos

        #     # Pour chaque pixel de l'image {
        tabx = np.linspace(screen[0], screen[2], num=width+1)
        tabx = (tabx[:-1] + tabx[1:]) / 2 # Get center of pixels
        taby = np.linspace(screen[1], screen[3], num=height+1)
        taby = (taby[:-1] + taby[1:]) / 2 # Get center of pixels
        for i, y in (enumerate(tqdm(taby))):
            for j, x in (enumerate(tabx)):

                pixelPos = l2n((x, y, 0, 1))
                pixelPos = n2l(tr_mat@pixelPos)
                pixelPos = (pixelPos[0], pixelPos[1], pixelPos[2])
                
                direction = l2n(pixelPos) - l2n(cam_pos) #TODO : Changer focal pour endroit du pixel
                direction = direction / np.linalg.norm(direction)
                
                pixelColor = (0,0,0)
                
                
                
                # Créer un rayon qui, de l'oeil, passe par ce pixel
                pointRayTarget = n2l(l2n(cam_pos) + RayCastLength*direction)

                if isHit(self.obbTree, cam_pos, pointRayTarget):
                    pointsInter, cellIdsInter = GetIntersect(self.obbTree,
                                                             cam_pos,
                                                             pointRayTarget)
                    # TODO : Garder le plus proche des points d'intersect
                    # ANSWER TODO : C'est le pointsInter[0]; pointsInter étant la liste de tous les points d'intersections, le [0] c'est le premier

                    normalModel = self.normalsModel.GetTuple(cellIdsInter[0])

                    vecInc = l2n(pointsInter[0] - l2n(cam_pos)) # Vector from cam to intersect
                    vecInc = n2l(vecInc / np.linalg.norm(vecInc))

                    # Calculate the reflected ray vector
                    #vecRef = calcVecR(vecInc, normalModel)
                    #vecRef = vecRef / np.linalg.norm(vecRef)
                    # recursive call here

                    pixelColor = clip(n2l(self.radianceAtPoint(vecInc, pointsInter[0], normalModel, 0, max_depth=max_depth)))
                
                else:

                #si 0 points d'intersections :
                    # Couleur ce pixel avec la couleur d'arrière-plan
                    pixelColor = self.renderer.GetBackground()

                # for k in range(max_depth):
                image[i, j] = pixelColor
                    

        print("Generating picture...")
            
        plt.imsave("output.png", image)
        
        self.renderer.AddActor(self.sun_actor)
        self.renderer.AddActor(self.glyphActorSun)
        self.render_window.Render()

        print("Done !")

    def radianceAtPoint(self, ray_origin, point, N, depth, max_depth=1, n_reflects=1):
        #Si on a atteint la profondeur max, on utilise la contribution directe
        # de la lumière
        if (depth >= max_depth):
            if isHit(self.obbTree, self.pos_Light, point):
                return l2n((0, 0, 0))
            else:
                # return self.light.GetDiffuseColor() #TODO : Get dynamic light color
                return l2n((1,1,1))
                
        else:
            ray_dir = calcVecR(ray_origin, N)
            out_ray_point = n2l(l2n(point) + RayCastLength*l2n(ray_dir))
            point = n2l(l2n(N) * 1e-5 + l2n(point)) # To avoid hitting itself

            if isHit(self.obbTree, point, out_ray_point):
                pointsInter, cellIdsInter = GetIntersect(self.obbTree,
                                                            point,
                                                            out_ray_point)

                nextN = self.normalsModel.GetTuple(cellIdsInter[0])
                
                intersection_to_light = l2n(self.pos_Light) - l2n(pointsInter[0])
                intersection_to_light /= np.linalg.norm(intersection_to_light)

                if isHit(self.obbTree, self.pos_Light, point):
                    direct_illumination = l2n((1, 1, 1)) # Change later
                else:
                    direct_illumination = l2n((0, 0, 0))

                # Calculate the reflected ray vector

                #TODO : il faut set les specular et diffuse color du material au début
                #Ou juste utiliser color ?
                # ambientMat = l2n(self.powerplant_actor.GetProperty().GetAmbientColor())
                ambientMat = l2n(self.powerplant_actor.GetProperty().GetColor())
                # specularMat = l2n(self.powerplant_actor.GetProperty().GetSpecularColor())
                specularMat = l2n(self.powerplant_actor.GetProperty().GetColor())
                # diffuseMat = l2n(self.powerplant_actor.GetProperty().GetDiffuseColor())
                diffuseMat = l2n(self.powerplant_actor.GetProperty().GetColor())


                intensity = self.light.GetIntensity()
                ambientLight = l2n(self.light.GetAmbientColor()) * intensity
                specularLight = l2n(self.light.GetSpecularColor()) * intensity
                diffuseLight = l2n(self.light.GetDiffuseColor()) * intensity

                # Initialize color
                # ambiant
                illumination = ambientMat * ambientLight

                # diffuse
                illumination += diffuseMat * diffuseLight * np.dot(intersection_to_light, N) * direct_illumination

                # specular
                intersection_to_origin = ray_origin - l2n(pointsInter[0])
                intersection_to_origin /= np.linalg.norm(intersection_to_origin)
                
                H = intersection_to_light + intersection_to_origin
                H /= np.clip(np.linalg.norm(H), 0, 1)
                
                illumination += specularMat * specularLight * np.dot(l2n(N), H) ** (100 / 4)

                reflection = 0.8

                return illumination + reflection * self.radianceAtPoint(point, pointsInter[0], nextN, depth + 1, max_depth=max_depth)
                return color + self.radianceAtPoint(pointsInter[0], vecRef, depth + 1, cam_pos, max_depth=max_depth)
                # TODO : Here, find the material and lambert part + how to sample rays
                # terms = []
                # for n in range(n_reflects):
                
                incoming_light_ray = l2n(self.radianceAtPoint(pointsInter[0], vecRef, depth + 1, max_depth=max_depth))
                # lambert = 1 # Easy to compute 
                # material = 1 # Hard to find in vtk
                # terms.append(incoming_light_ray * material * lambert)
                
                # incoming_light = np.mean(np.asarray(terms), axis=0)
                # return n2l(incoming_light * material * lambert)

            else: # Reflext background color, here black so no background color
                return l2n((0, 0, 0))
        return 0

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
