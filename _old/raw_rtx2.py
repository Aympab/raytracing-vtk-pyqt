# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 20:59:12 2015
 
Preliminary code for ray tracing with python
prereq: vtk.
Thanks to https://pyscience.wordpress.com/2014/10/05/from-ray-casting-to-ray-tracing-with-python-and-vtk/
 
In order to proceed, you will have to exit the renderwindow, it is waiting for your input.
 
@author: jaap
"""
 
import vtk
import numpy as np
import matplotlib.pyplot as plt
 
 
RayCastLength = 100
ColorRay = [1.0, 1.0, 0.0]
ColorRayMiss = [1.0, 1.0, 1.0]
 
l2n = lambda l: np.array(l)
n2l = lambda n: list(n)
 
def addPoint(ren, appendFilter, p, color=[0.0, 0.0, 0.0], radius=0.2, ):
    point = vtk.vtkSphereSource()
    point.SetCenter(p)
    point.SetRadius(radius)
    point.SetPhiResolution(100)
    point.SetThetaResolution(100)
    # map point
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(point.GetOutputPort())
    # set actor for point
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    #draw point in renderer
    ren.AddActor(actor)
    #appendFilter.AddInput(line.GetOutput())
    #appendFilter.Update()
 
def addLine(ren, appendFilter, p1, p2, color=[0.0, 0.0, 1.0], opacity=1.0):
    line = vtk.vtkLineSource()
    line.SetPoint1(p1)
    line.SetPoint2(p2)
 
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(line.GetOutputPort())
 
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty()
 
    ren.AddActor(actor)
    
    appendFilter.AddInput(line.GetOutput())
    appendFilter.Update()
 
 
def isHit(obbTree, pSource, pTarget):
    """Returns True if the line intersects with the mesh in 'obbTree'"""
    code = obbTree.IntersectWithLine(pSource, pTarget, None, None)
    if code == 0:
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
    assert (code != 0)
    # Get point-data 
    pointData = points.GetData()
    # Get number of intersection points found
    noPoints = pointData.GetNumberOfTuples()
    # Get number of intersected cell ids
    noIds = cellIds.GetNumberOfIds()
    
    assert (noPoints == noIds)
    assert (noPoints > 0)
    # Loop through the found points and cells and store
    # them in lists
    pointsInter = []
    cellIdsInter = []
    for idx in range(noPoints):
        pointsInter.append(pointData.GetTuple3(idx))
        cellIdsInter.append(cellIds.GetId(idx))
    
    return pointsInter, cellIdsInter
 
def calcVecReflect(vecInc, vecNor):
    '''    
    http://graphics.stanford.edu/courses/cs148-10-summer/docs/2006--degreve--reflection_refraction.pdf
    Vector reflect(const Vector& normal, const Vactor& incident)
    {
        const double cosI = -dot(normal, incident);
        return incident + 2 * cosI * normal;
    }  
    '''
    vecInc = l2n(vecInc)
    vecNor = l2n(vecNor)
    cosI = -np.dot(vecNor, vecInc)
    vecRef = vecInc + 2*cosI*vecNor
    return n2l(vecRef)
 
 
def calcVecRefract(vecInc, vecNor, n1=1.0, n2=1.33):
    '''
    http://graphics.stanford.edu/courses/cs148-10-summer/docs/2006--degreve--reflection_refraction.pdf
    Vector refract(Const Vector& normal, const Vector& incident, double n1, double n2)
    {
        const double n = n1/n2;
        const double cosI = -dot(normal, incident)
        const double sinT2 = n*n*(1.0-cosI*cosI);
        if (sinT2 > 1.0) return Vactor::invalid; //TIR
        const double cosT = sqrt(1.0 - sinT2);
        return n * incident + (n * cosI - cosT) * normal;
    }
    n1 = first medium, n2 is second medium
    '''
    n=n1/n2
    vecInc = l2n(vecInc)
    vecNor = l2n(vecNor)    
    cosI = -np.dot(vecNor, vecInc)
    sinT2 = n**2*(1-cosI**2)
    assert (sinT2 < 1.0)
    if sinT2 < 1.0:
        cosT = np.sqrt(1.0-sinT2)
        vecRef = n * vecInc + (n * cosI - cosT) * vecNor
        return n2l(vecRef)
    else:
        return 'blah'
 
def vtkspheresource(ren, appendFilter, srf ):
    # Create and configure sphere, radius is focalpoint
    location = [0.0,0.0,0.0] #It's the source, so location is zero    
    startendtheta = 180*np.arcsin(0.5*srf['diam']/srf['fp'])/np.pi  
    print(startendtheta)
    sphere = vtk.vtkSphereSource()
    sphere.SetCenter(location)
    sphere.SetRadius(srf['fp'])
    sphere.SetThetaResolution(srf['resolution']*3)
    sphere.SetPhiResolution(srf['resolution'])
    #sphere.SetStartTheta(90-startendtheta)  # create partial sphere
    #sphere.SetEndTheta(90+startendtheta)     
    sphere.SetStartPhi(180-startendtheta)  # create partial sphere
    sphere.SetEndPhi(180)   
    # rotate and move such that the source goes through 0,0,0 and is oriented along the z axis
    transform = vtk.vtkTransform()
    transform.RotateWXYZ(180,1,0,0)
    transform.Translate(0.0,0.0,srf['fp'])
    transformFilter=vtk.vtkTransformPolyDataFilter()
    transformFilter.SetTransform(transform)
    transformFilter.SetInputConnection(sphere.GetOutputPort())
    transformFilter.Update()
    # Create mapper and set the mapped texture as input
    mapperSphere = vtk.vtkPolyDataMapper()
    # mapperSphere.SetInputData(transformFilter.GetOutput())
    # Create actor and set the mapper and the texture
    actorSphere = vtk.vtkActor()
    actorSphere.SetMapper(mapperSphere)
    actorSphere.GetProperty().SetColor([1.0, 0.0, 0.0])  #set color to yellow
    actorSphere.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
    actorSphere.GetProperty().SetEdgeColor([0.0, 0.0, 0.0])  #render edges as white
    #Create points
    cellCenterCalcSource = vtk.vtkCellCenters()
    # cellCenterCalcSource.SetInput(transformFilter.GetOutput())
    cellCenterCalcSource.Update()
    # Get the point centers from 'cellCenterCalc'
    pointsCellCentersSource = cellCenterCalcSource.GetOutput(0)
    # dummy point container
    normal_points = vtk.vtkPoints()
    # Loop through all point centers and add a point-actor through 'addPoint'
    for idx in range(pointsCellCentersSource.GetNumberOfPoints()):
        addPoint(ren, False, pointsCellCentersSource.GetPoint(idx), [1.0, 1.0, 0.0])
        normal_points.InsertNextPoint(pointsCellCentersSource.GetPoint(idx))
    
    # Create a new 'vtkPolyDataNormals' and connect to the 'Source' half-sphere
    normalsCalcSource = vtk.vtkPolyDataNormals()
    normalsCalcSource.SetInputConnection(transformFilter.GetOutputPort())
    # Disable normal calculation at cell vertices
    normalsCalcSource.ComputePointNormalsOff()
    # Enable normal calculation at cell centers
    normalsCalcSource.ComputeCellNormalsOn()
    # Disable splitting of sharp edges
    normalsCalcSource.SplittingOff()
    # Disable global flipping of normal orientation
    normalsCalcSource.FlipNormalsOff()
    # Enable automatic determination of correct normal orientation
    normalsCalcSource.AutoOrientNormalsOn()
    # Perform calculation
    normalsCalcSource.Update()
    '''# Test glyphs,   turned off for now
    glyphsa = glyphnormals(refract_polydata)
    ren.AddActor(glyphsa)'''
    # Plot and save
    ren.AddActor(actorSphere)
    # appendFilter.AddInput(transformFilter.GetOutput())
    appendFilter.Update()
    # set camera properties
    camera = ren.MakeCamera()
    camera.SetPosition(-100, 100, 100)
    camera.SetFocalPoint(0.0, 0.0, 0.0)
    camera.SetViewAngle(30.0)
    ren.SetActiveCamera(camera)
    return transformFilter, normal_points, normalsCalcSource
 
def glyphnormals(ren, normals):
    # this doesn't work, it will always go to the normal, 
    dummy_cellCenterCalcSource = vtk.vtkCellCenters()
    dummy_cellCenterCalcSource.VertexCellsOn()
    dummy_cellCenterCalcSource.SetInputConnection(normals.GetOutputPort())
    # Create a new 'default' arrow to use as a glyph
    arrow = vtk.vtkArrowSource()
    # Create a new 'vtkGlyph3D'
    glyphSource = vtk.vtkGlyph3D()
    # Set its 'input' as the cell-center normals calculated at the Source's cells
    glyphSource.SetInputConnection(dummy_cellCenterCalcSource.GetOutputPort())
    # Set its 'source', i.e., the glyph object, as the 'arrow'
    glyphSource.SetSourceConnection(arrow.GetOutputPort())
    # Enforce usage of normals for orientation
    glyphSource.SetVectorModeToUseNormal()
    # Set scale for the arrow object
    glyphSource.SetScaleFactor(1)
    # Create a mapper for all the arrow-glyphs
    glyphMapperSource = vtk.vtkPolyDataMapper()
    glyphMapperSource.SetInputConnection(glyphSource.GetOutputPort())
    # Create an actor for the arrow-glyphs
    glyphActorSource = vtk.vtkActor()
    glyphActorSource.SetMapper(glyphMapperSource)
    glyphActorSource.GetProperty().SetColor([1.0,1.0,0.0])
    # Add actor
    ren.AddActor(glyphActorSource)
 
def glyphs(cells):
    # Visualize normals as done previously but using refracted or reflected cells
    arrow = vtk.vtkArrowSource()
    glyphCell = vtk.vtkGlyph3D()
    glyphCell.SetInput(cells)
    glyphCell.SetSourceConnection(arrow.GetOutputPort())
    glyphCell.SetVectorModeToUseNormal()
    glyphCell.SetScaleFactor(1)
    
    glyphMapperCell = vtk.vtkPolyDataMapper()
    glyphMapperCell.SetInputConnection(glyphCell.GetOutputPort())
    
    glyphActorCell = vtk.vtkActor()
    glyphActorCell.SetMapper(glyphMapperCell)
    glyphActorCell.GetProperty().SetColor([1.0,1.0,1.0])
    return glyphActorCell
 
 
def vtklenssurface(ren, appendFilter, srf):
    phi = 180*np.arcsin(0.5*srf['diam']/srf['fp'])/np.pi
    lensA = vtk.vtkSphereSource()
    lensA.SetCenter(0.0, 0.0, 0.0) #we will move it later
    lensA.SetThetaResolution(100)
    lensA.SetPhiResolution(20)
    lensA.SetRadius(srf['fp'])
    lensA.SetStartPhi(180-phi)  # create partial sphere
    lensA.SetEndPhi(180)
    #Transform
    transform = vtk.vtkTransform()
    if srf['curv'] == 'positive':
        location = srf['location'][:]
        location[2] = srf['location'][2]+srf['fp'] #if I want the location exactly, h=R-np.sqrt(R**2-(w/2)**2)
        transform.Translate(location)        
        print(location)
        print(srf['location'])
    elif srf['curv'] == 'negative':
        #Transform
        transform.RotateWXYZ(180,1,0,0)
        lensBt=vtk.vtkTransformPolyDataFilter()
        lensBt.SetTransform(transform)
        lensBt.SetInputConnection(lensA.GetOutputPort())
        lensBt.Update()
        location = srf['location'][:]
        location[2] = srf['location'][2]-srf['fp'] #if I want the location exactly, h=R-np.sqrt(R**2-(w/2)**2)
        lensA = lensBt
        transform = vtk.vtkTransform() #redfine transform
        transform.Translate(location)
        print(location)
        print(srf['location'])
    else:
        print("not negative or positive")
    
    lensAt=vtk.vtkTransformPolyDataFilter()
    lensAt.SetTransform(transform)
    lensAt.SetInputConnection(lensA.GetOutputPort())
    lensAt.Update()
    # Map 
    lensAm = vtk.vtkPolyDataMapper()
    lensAm.SetInput(lensAt.GetOutput())
    # Create actor
    lensAa = vtk.vtkActor()
    lensAa.SetMapper(lensAm)
    lensAa.GetProperty().SetColor([0.0,0.0,1.0])  #set color to yellow
    lensAa.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
    lensAa.GetProperty().SetEdgeColor([1.0,1.0,1.0])  #render edges as white
    # Plot and save
    ren.AddActor(lensAa)
    appendFilter.AddInput(lensAt.GetOutput())
    appendFilter.Update()
    # set camera properties
    camera = ren.MakeCamera()
    camera.SetPosition(-100, 100, 100)
    camera.SetFocalPoint(location)
    camera.SetViewAngle(30.0)
    ren.SetActiveCamera(camera)
    return lensAt
 
def vtkscreen(ren, appendFilter, screen):
    # Create a pentagon
    flat = vtk.vtkRegularPolygonSource()
    #polygonSource.GeneratePolygonOff()
    flat.SetNumberOfSides(4)
    flat.SetRadius(screen['width'])
    flat.SetCenter(screen['center'])
    flat.Update()
     # Create mapper and set the mapped texture as input
    flatm = vtk.vtkPolyDataMapper()
    flatm.SetInputConnection(flat.GetOutputPort())
    flata = vtk.vtkActor()
    # Create actor and set the mapper and the texture
    flata.SetMapper(flatm)
    flata.GetProperty().SetColor([0.3,0.3,0.3])  #set color to grey
    flata.GetProperty().EdgeVisibilityOn()  # show edges/wireframe
    flata.GetProperty().SetEdgeColor([1.0,1.0,1.0])  #render edges as white
    # Plot and save
    ren.AddActor(flata)
    appendFilter.AddInput(flat.GetOutput())
    appendFilter.Update()
    # set camera properties
    camera = ren.MakeCamera()
    camera.SetPosition(-100, 100, 100)
    camera.SetFocalPoint(screen['center'])
    camera.SetViewAngle(30.0)
    ren.SetActiveCamera(camera)
    return flat
 
# get info for rays, they go through the mesh nodes.
def refract(ren, appendFilter, surface1, surface2):
    surf2 = surface2['surface']
    #normalsSource = normalsCalcSource.GetOutput().GetCellData().GetNormals()
    pointsCellCentersSurf1 = surface1['normalpoints']
    if 'refractcells' in surface1:  #technically it is a bit weird that you have to specify which vectors are the right ones, 
        normalsCalcSurf1 = surface1['refractcells'] 
        # vectors of refracted rays        
        normalsSurf1 = normalsCalcSurf1.GetPointData().GetNormals()
    elif 'refractcells' not in surface1 and 'normalcells' in surface1:
        normalsCalcSurf1 = surface1['normalcells']
        # vectors of normal rays
        normalsSurf1 = normalsCalcSurf1.GetOutput().GetCellData().GetNormals()
    else:
        print("problem in surface 1 input parameters function refract"        )
    # If 'points' and 'source' are known, then use these.
    # They have to be known, otherwise the wrong order is used. So skip
    # prepare for raytracing
    obbsurf2 = vtk.vtkOBBTree()
    obbsurf2.SetDataSet(surf2.GetOutput())
    obbsurf2.BuildLocator()
    
    # Create a new 'vtkPolyDataNormals' and connect to the target surface
    normalsCalcSurf2 = vtk.vtkPolyDataNormals()
    normalsCalcSurf2.SetInputConnection(surf2.GetOutputPort())
    # Disable normal calculation at cell vertices
    normalsCalcSurf2.ComputePointNormalsOff()
    # Enable normal calculation at cell centers
    normalsCalcSurf2.ComputeCellNormalsOn()
    # Disable splitting of sharp edges
    normalsCalcSurf2.SplittingOff()
    # Disable global flipping of normal orientation for negative curvature
    if 'curv' in surface2:    
        if surface2['curv'] is 'positive':
            normalsCalcSurf2.FlipNormalsOff()
        elif surface2['curv'] is 'negative':
            normalsCalcSurf2.FlipNormalsOn()        
        else:
            print("Problem in surface 2 input parameter curve, function refract")
    # Enable automatic determination of correct normal orientation
    normalsCalcSurf2.AutoOrientNormalsOn()
    # Perform calculation
    normalsCalcSurf2.Update()
    # Extract the normal-vector data at the target surface
    normalsSurf2 = normalsCalcSurf2.GetOutput().GetCellData().GetNormals()
    
    # where intersections are found
    intersection_points = vtk.vtkPoints()
    # vectors where intersections are found
    normal_vectors = vtk.vtkDoubleArray()
    normal_vectors.SetNumberOfComponents(3)
    # normals of refracted vectors
    refract_vectors = vtk.vtkDoubleArray()
    refract_vectors.SetNumberOfComponents(3)
    refract_polydata = vtk.vtkPolyData()
    
    # Loop through all of Source's cell-centers
    for idx in range(pointsCellCentersSurf1.GetNumberOfPoints()):
        # Get coordinates of Source's cell center
        pointSurf1 = pointsCellCentersSurf1.GetPoint(idx)
        # Get normal vector at that cell
        normalsurf1 = normalsSurf1.GetTuple(idx)
        # Calculate the 'target' of the ray based on 'RayCastLength'
        pointRaySurf2 = n2l(l2n(pointSurf1) + RayCastLength*l2n(normalsurf1))
        # Check if there are any intersections for the given ray
        if isHit(obbsurf2, pointSurf1, pointRaySurf2):
            # Retrieve coordinates of intersection points and intersected cell ids
            pointsInter, cellIdsInter = GetIntersect(obbsurf2, pointSurf1, pointRaySurf2)
            # Render lines/rays emanating from the Source. Rays that intersect are
            addLine(ren, appendFilter, pointSurf1, pointsInter[0], ColorRay, opacity=0.25)
            # Render intersection points
            addPoint(ren, False, pointsInter[0], ColorRay)
            # Get the normal vector at the surf2 cell that intersected with the ray
            normalsurf2 = normalsSurf2.GetTuple(cellIdsInter[0])
            # Insert the coordinates of the intersection point in the dummy container
            intersection_points.InsertNextPoint(pointsInter[0])
            # Insert the normal vector of the intersection cell in the dummy container
            normal_vectors.InsertNextTuple(normalsurf2)
            # Calculate the incident ray vector
            vecInc = n2l(l2n(pointRaySurf2) - l2n(pointSurf1))
            # Calculate the reflected ray vector
            #vecRef = calcVecReflect(vecInc, normallensA)
            vecRef = calcVecRefract(vecInc/np.linalg.norm(vecInc), normalsurf2, surface1['rn'], surface2['rn'])
            refract_vectors.InsertNextTuple(vecRef)
            ## Calculate the 'target' of the reflected ray based on 'RayCastLength'
            #pointRayReflectedTarget = n2l(l2n(pointsInter[0]) + RayCastLength*l2n(vecRef))
            ##pointRayReflectedTarget = n2l(l2n(pointsInter[0]) - RayCastLength*l2n(vecRef))
            ## Render lines/rays bouncing off lensA with a 'ColorRayReflected' color
            #addLine(ren, pointsInter[0], pointRayReflectedTarget, ColorRay)
            
    # export normals at lens surface
    normalsCalcSurface2 = vtk.vtkPolyDataNormals()
    normalsCalcSurface2.SetInputConnection(surf2.GetOutputPort())
    # Disable normal calculation at cell vertices
    normalsCalcSurface2.ComputePointNormalsOff()
    # Enable normal calculation at cell centers
    normalsCalcSurface2.ComputeCellNormalsOn()
    # Disable splitting of sharp edges
    normalsCalcSurface2.SplittingOff()
    # Disable global flipping of normal orientation
    normalsCalcSurface2.FlipNormalsOff()
    # Enable automatic determination of correct normal orientation
    normalsCalcSurface2.AutoOrientNormalsOn()
    # Perform calculation
    normalsCalcSurface2.Update()
    # Create a dummy 'vtkPolyData' to store refracted vecs
    refract_polydata.SetPoints(intersection_points)
    refract_polydata.GetPointData().SetNormals(refract_vectors)
    # Return data for next surface, all has been drawn
    '''# Test glyphs,   turned off for now
    glyphsa = glyphs(refract_polydata)
    ren.AddActor(glyphsa)
    '''
    return intersection_points, normalsCalcSurface2,  refract_polydata
 
# get info for rays, they go through the mesh nodes.
def reflect(ren, appendFilter, surface1, surface2):
    surf2 = surface2['surface']
    pointsCellCentersSurf1 = surface1['normalpoints']
    if 'refractcells' in surface1:  #technically it is a bit weird that you have to specify which vectors are the right ones, 
        normalsCalcSurf1 = surface1['refractcells'] 
        # vectors of refracted rays        
        normalsSurf1 = normalsCalcSurf1.GetPointData().GetNormals()
    elif 'reflectcells' in surface1:
        normalsCalcSurf1 = surface1['reflectcells']
        # vectors of reflected rays        
        normalsSurf1 = normalsCalcSurf1.GetPointData().GetNormals()
    elif 'refractcells' not in surface1 and 'reflectcells' not in surface1 and 'normalcells' in surface1:
        normalsCalcSurf1 = surface1['normalcells']
        # vectors of normal rays
        normalsSurf1 = normalsCalcSurf1.GetOutput().GetCellData().GetNormals()
    else:
        print("problem in surface 1 input parameters function refract")
    # If 'points' and 'source' are known, then use these.
    # They have to be known, otherwise the wrong order is used. So skip
    # prepare for raytracing
    obbsurf2 = vtk.vtkOBBTree()
    obbsurf2.SetDataSet(surf2.GetOutput())
    obbsurf2.BuildLocator()
 
    # Create a new 'vtkPolyDataNormals' and connect to the target surface
    normalsCalcSurf2 = vtk.vtkPolyDataNormals()
    normalsCalcSurf2.SetInputConnection(surf2.GetOutputPort())
    # Disable normal calculation at cell vertices
    normalsCalcSurf2.ComputePointNormalsOff()
    # Enable normal calculation at cell centers
    normalsCalcSurf2.ComputeCellNormalsOn()
    # Disable splitting of sharp edges
    normalsCalcSurf2.SplittingOff()
    # Disable global flipping of normal orientation for negative curvature
    if 'curv' in surface2:    
        if surface2['curv'] is 'positive':
            normalsCalcSurf2.FlipNormalsOff()
        elif surface2['curv'] is 'negative':
            normalsCalcSurf2.FlipNormalsOn()        
        else:
            print("Problem in surface 2 input parameter curve, function refract")
    # Enable automatic determination of correct normal orientation
    normalsCalcSurf2.AutoOrientNormalsOn()
    # Perform calculation
    normalsCalcSurf2.Update()
    # Extract the normal-vector data at the target surface
    normalsSurf2 = normalsCalcSurf2.GetOutput().GetCellData().GetNormals()
   
    # where intersections are found
    intersection_points = vtk.vtkPoints()
    # vectors where intersections are found
    normal_vectors = vtk.vtkDoubleArray()
    normal_vectors.SetNumberOfComponents(3)
    # normals of refracted vectors
    reflect_vectors = vtk.vtkDoubleArray()
    reflect_vectors.SetNumberOfComponents(3)
    reflect_polydata = vtk.vtkPolyData()
    
    # Loop through all of Source's cell-centers
    for idx in range(pointsCellCentersSurf1.GetNumberOfPoints()):
        # Get coordinates of Source's cell center
        pointSurf1 = pointsCellCentersSurf1.GetPoint(idx)
        # Get normal vector at that cell
        normalsurf1 = normalsSurf1.GetTuple(idx)
        # Calculate the 'target' of the ray based on 'RayCastLength'
        pointRaySurf2 = n2l(l2n(pointSurf1) + RayCastLength*l2n(normalsurf1))
        # Check if there are any intersections for the given ray
        if isHit(obbsurf2, pointSurf1, pointRaySurf2):
            # Retrieve coordinates of intersection points and intersected cell ids
            pointsInter, cellIdsInter = GetIntersect(obbsurf2, pointSurf1, pointRaySurf2)
            # Render lines/rays emanating from the Source. Rays that intersect are
            addLine(ren, appendFilter, pointSurf1, pointsInter[0], ColorRay, opacity=0.25)
            # Render intersection points
            addPoint(ren, False, pointsInter[0], ColorRay)
            # Get the normal vector at the surf2 cell that intersected with the ray
            normalsurf2 = normalsSurf2.GetTuple(cellIdsInter[0])
            # Insert the coordinates of the intersection point in the dummy container
            intersection_points.InsertNextPoint(pointsInter[0])
            # Insert the normal vector of the intersection cell in the dummy container
            normal_vectors.InsertNextTuple(normalsurf2)
            # Calculate the incident ray vector
            vecInc = n2l(l2n(pointRaySurf2) - l2n(pointSurf1))
            # Calculate the reflected ray vector
            vecRef = calcVecReflect(vecInc/np.linalg.norm(vecInc), normalsurf2)
            #vecRef = calcVecRefract(vecInc/np.linalg.norm(vecInc), normalsurf2, surface1['rn'], surface2['rn'])
            reflect_vectors.InsertNextTuple(vecRef)
            ## Calculate the 'target' of the reflected ray based on 'RayCastLength'
            #pointRayReflectedTarget = n2l(l2n(pointsInter[0]) + RayCastLength*l2n(vecRef))
            ##pointRayReflectedTarget = n2l(l2n(pointsInter[0]) - RayCastLength*l2n(vecRef))
            ## Render lines/rays bouncing off lensA with a 'ColorRayReflected' color
            #addLine(ren, pointsInter[0], pointRayReflectedTarget, ColorRay)
            
    # export normals at surface
    normalsCalcSurface2 = vtk.vtkPolyDataNormals()
    normalsCalcSurface2.SetInputConnection(surf2.GetOutputPort())
    # Disable normal calculation at cell vertices
    normalsCalcSurface2.ComputePointNormalsOff()
    # Enable normal calculation at cell centers
    normalsCalcSurface2.ComputeCellNormalsOn()
    # Disable splitting of sharp edges
    normalsCalcSurface2.SplittingOff()
    # Disable global flipping of normal orientation
    normalsCalcSurface2.FlipNormalsOff()
    # Enable automatic determination of correct normal orientation
    normalsCalcSurface2.AutoOrientNormalsOn()
    # Perform calculation
    normalsCalcSurface2.Update()
    # Create a dummy 'vtkPolyData' to store refracted vecs
    reflect_polydata.SetPoints(intersection_points)
    reflect_polydata.GetPointData().SetNormals(reflect_vectors)
    # Return data for next surface, all has been drawn
    '''# Test glyphs,   turned off for now
    glyphsa = glyphs(refract_polydata)
    ren.AddActor(glyphsa)
    '''
    return intersection_points, normalsCalcSurface2,  reflect_polydata
 
 
def run(surfaces, project, Directory, scene, plot=1):
    ### write output to vtp file
    writer = vtk.vtkXMLPolyDataWriter()
    filename = Directory+project+"%04d.vtp" % Scene
    writer.SetFileName(filename)
    appendFilter = vtk.vtkAppendPolyData()
    
    ### Create a render window
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(600,600)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    iren.Initialize()
    rays = dict()
    for srf in surfaces:
        # Fill the scene
        if srf['type'] == 'source':
            #Draw source            
            srf['surface'], srf['normalpoints'], srf['normalcells'] = vtkspheresource(ren, appendFilter,srf)
            #Also draw glyphs to see where lines are going
            glyphnormals(ren, srf['normalcells'])
            renWin.Render()
            
        elif srf['type'] == 'lens' and 'normalcells' in rays:
            # Draw refractive surfaces
            srf['surface'] = vtklenssurface(ren, appendFilter, srf)
            renWin.Render()
            srf['normalpoints'], srf['normalcells'], srf['refractcells'] = refract(ren, appendFilter, rays, srf)
            renWin.Render()
            
        elif srf['type'] == 'screen' and 'normalcells' in rays :
            # Draw screen
            srf['surface'] = vtkscreen(ren, appendFilter, srf)
            renWin.Render()
            srf['normalpoints'], srf['normalcells'], srf['reflectcells'] = reflect(ren, appendFilter, rays, srf)
            renWin.Render()
            # Now plot the screen using matplotlib
            if plot == 1:
                # Get list from screen reflect cells
                plotlist = range(srf['normalpoints'].GetNumberOfPoints())
                for idx in range(srf['normalpoints'].GetNumberOfPoints()):
                    plotlist[idx] = srf['normalpoints'].GetPoint(idx)[0:2]
                
                plt.plot([cc[0] for cc in plotlist], [cc[1] for cc in plotlist], '.')
        rays = srf.copy()
    point = vtk.vtkSphereSource()
    point.SetRadius(1)
    point.SetCenter(0.0,0.0,30.0)
    pointm = vtk.vtkPolyDataMapper()
    pointm.SetInput(point.GetOutput())
    pointa = vtk.vtkActor()
    pointa.SetMapper(pointm)
    ren.AddActor(pointa)
    renWin.Render()
    
    '''# export scene to image
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(renWin)
    w2if.Update()        
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(Directory+project+"%04d.png" % Scene)
    writer.SetInput(w2if.GetOutput())
    writer.Write() '''
    ### write output to vtp file
    polydatacontainer = appendFilter
    writer.SetInput(polydatacontainer.GetOutput())
    writer.Write()
    # Check results in viewer, by exit screen, proceed
    iren.Start()
    #del renWin, iren
    
#end def main  
# del iren, renWin
surfaces = [{'type' :'source',
             'fp' :1e3,
             'diam' : 10,
             'resolution': 4,
             'rn': 1.0 },
             {'type' :'lens',
             'fp' :75,
             'diam' : 25,
             'location': [0.0, 0.0, 30],
             'rn': 1.5,
             'curv': 'positive' },    # a positive curvature means the focal point is further from the source than the location
            {'type': 'lens',
             'fp' :75,
             'diam' : 25,
             'location': [0.0, 0.0, 33],
             'rn': 1.0,
             'curv': 'negative'},    # a positive curvature means the focal point is further from the source than the location
            {'type': 'screen',
             'width': 50,
             'height': 50,
             'center': [0.0, 0.0, 130.0],  # Only using z, I can still only deal with center axis optics         
             'normal': [0.0, 0.0, -1.0] }]  # Not using, the screen is normal on the central axis
 
#assert 180*np.arcsin(0.5*source['diam']/source['fp'])/np.pi, "source is not well defined"  
 
project = 'test'
Directory = '/home/jaap/Spyder/optics/'
Scene = 0
run(surfaces, project, Directory, Scene, plot=0)
#del iren, renWin
 
Scene  = 1
surfaces[1]['location'] = [0.0, 2.0, 30] 
surfaces[2]['location'] = [0.0, 2.0, 33] 
run(surfaces, project, Directory, Scene, plot=0)
#del iren, renWin
 
Scene  = 2
surfaces[1]['location'] = [0.0, 4.0, 30] 
surfaces[2]['location'] = [0.0, 4.0, 33] 
run(surfaces, project, Directory, Scene, plot=0)