from audioop import lin2alaw
from vtkmodules.vtkRenderingCore import vtkTexture
from vtkmodules.vtkIOImage import vtkImageReader2Factory
from vtkmodules.vtkImagingCore import vtkImageFlip
import vtk
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
import numpy as np

l2n = lambda l: np.array(l)
n2l = lambda n: list(n)

def normalize(vector):
    return vector/np.linalg.norm(vector)

def calcVecR(vecInc, vecNor):
    vecInc = l2n(vecInc)
    vecNor = l2n(vecNor)
    
    vecRef = vecInc - 2*np.dot(vecInc, vecNor)*vecNor
    
    return n2l(vecRef)

def MakeAxesActor():
    axes = vtkAxesActor()
    axes.SetShaftTypeToCylinder()
    axes.SetXAxisLabelText('X')
    axes.SetYAxisLabelText('Y')
    axes.SetZAxisLabelText('Z')
    axes.SetTotalLength(100.0, 100.0, 100.0)
    axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
    axes.SetConeRadius(1.025 * axes.GetConeRadius())
    axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
    return axes

def addLine(renderer, p1, p2, color=[0.0, 0.0, 1.0], opacity=1):
    line = vtk.vtkLineSource()
    line.SetPoint1(p1)
    line.SetPoint2(p2)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(line.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)
    # renderer.AddActor(actor)
    
    return actor, line

def addPoint(renderer, p, radius=5.0, color=[0.0, 0.0, 0.0], resolution=100):
    point = vtk.vtkSphereSource()
    point.SetCenter(p)
    point.SetRadius(radius)
    point.SetPhiResolution(resolution)
    point.SetThetaResolution(resolution)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(point.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)

    renderer.AddActor(actor)
    
    return actor, point

def read_cubemap(folder_root, file_names):
    """
    Read six images forming a cubemap.
    :param folder_root: The folder where the cube maps are stored.
    :param file_names: The names of the cubemap files.
    :return: The cubemap texture.
    """
    texture = vtkTexture()
    texture.CubeMapOn()
    # Build the file names.
    fns = list()
    for fn in file_names:
        fns.append(folder_root.joinpath(fn))
        if not fns[-1].is_file():
            print('Nonexistent texture file:', fns[-1])
            return None
    i = 0
    for fn in fns:
        # Read the images.
        reader_factory = vtkImageReader2Factory()
        img_reader = reader_factory.CreateImageReader2(str(fn))
        img_reader.SetFileName(str(fn))

        flip = vtkImageFlip()
        flip.SetInputConnection(img_reader.GetOutputPort())
        flip.SetFilteredAxis(1)  # flip y axis
        texture.SetInputConnection(i, flip.GetOutputPort(0))
        i += 1

    texture.MipmapOn()
    texture.InterpolateOn()
    return texture

def isHit(obbTree, pSource, pTarget):
    r"""Returns True if the line intersects with the mesh in 'obbTree'"""
    code = obbTree.IntersectWithLine(pSource, pTarget, None, None)
    if code==0:
        return False
    return True

def GetIntersect(obbTree, pSource, pTarget):
    
    # Create an empty 'vtkPoints' object to store the intersection point coordinates
    points = vtk.vtkPoints()
    # Create an empty 'vtkIdList' object to store the ids of the cells that intersect
    # with the cast rays
    cellIds = vtk.vtkIdList()
    
    # Perform intersection
    code = obbTree.IntersectWithLine(pSource, pTarget, points, cellIds)
    
    # Get point-data 
    pointData = points.GetData()
    # Get number of intersection points found
    noPoints = pointData.GetNumberOfTuples()
    # Get number of intersected cell ids
    noIds = cellIds.GetNumberOfIds()
    
    assert (noPoints == noIds)
    
    # Loop through the found points and cells and store
    # them in lists
    pointsInter = []
    cellIdsInter = []
    for idx in range(noPoints):
        pointsInter.append(pointData.GetTuple3(idx))
        cellIdsInter.append(cellIds.GetId(idx))
    
    return pointsInter, cellIdsInter

def clip(l):
    for i, e in enumerate(l) :
        l[i] = min(1, max(0,e))
    return l

# def BRDF(matSpecular, matAmbient, matDiffuse):
    

# def compute_rtx(scene, cameraP, cameraFocus, lightP, resolution = 256):
    
    
    
    
# Pour chaque pixel de l'image {
#     Créer un rayon qui, de l'œil, passe par ce pixel
#     Initialiser « NearestT » à « INFINITY » et « NearestObject » à « NULL »

#     Pour chaque objet de la scène {
#         Si le faisceau frappe cet objet {
#             Si la distance « t » est inférieur à « NearestT » {
#                 Set "NearestT" à "t"
#                 Set « NearestObject » à cet objet
#             }
#         }
#     }

#     Si "NearestObject" est "NULL" {
#           Couleur ce pixel avec la couleur d'arrière-plan
#      Dans le cas contraire {}
#           Envoyer un rayon au niveau de chaque source de lumière pour tester si elle est à l'ombre
#           Si la surface est réfléchissante, le faisceau réfléchi génère: (récursion)
#           Si la surface est transparente, il génère le rayon réfracté: (récursion)
#           Utilisez « NearestObject » et « NearestT » pour calculer la couleur
#           Couleur ce pixel avec la couleur résultant
#       }
#   }
