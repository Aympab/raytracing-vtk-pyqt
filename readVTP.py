# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtk import vtkOBJReader, vtkSTLReader

def get_custom_parameters():
    import argparse
    description = 'Read a VTK XML PolyData file.'
    epilogue = ''''''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filename', help='horse.vtp.')
    args = parser.parse_args()
    if args.filename[-3:] == "vtp":
        filetype = "vtp"
    elif args.filename[-3:] == "obj":
        filetype = "obj"
    else:
        filetype = "unk"
    
    return args.filename, filetype


def readfile(filename, filetype):
    print(f"Reading {filename} with {filetype} type")
    if filetype == "obj":
        reader = vtkOBJReader()
    else:
        reader = vtkXMLPolyDataReader()

    reader.SetFileName(filename)
    reader.Update()

    return reader


def modelFromFile(filename):
    if filename[-3:] == "vtp":
        filetype = "vtp"
    elif filename[-3:] == "obj":
        filetype = "obj"
    else:
        filetype = "unk"

    reader = readfile(filename, filetype)
    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    
    colors = vtkNamedColors()

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d('Tan'))

    return mapper, actor

def loadOBJ(filenameOBJ):
    readerOBJ = vtkOBJReader()
    readerOBJ.SetFileName(filenameOBJ)
    # 'update' the reader i.e. read the .OBJ file
    readerOBJ.Update()

    polydata = readerOBJ.GetOutput()

    # If there are no points in 'vtkPolyData' something went wrong
    if polydata.GetNumberOfPoints() == 0:
        raise ValueError(
            "No point data could be loaded from '" + filenameOBJ)
        return None
    
    return polydata

def loadSTL(filenameSTL):
    readerSTL = vtkSTLReader()
    readerSTL.SetFileName(filenameSTL)
    # 'update' the reader i.e. read the .stl file
    readerSTL.Update()

    polydata = readerSTL.GetOutput()

    # If there are no points in 'vtkPolyData' something went wrong
    if polydata.GetNumberOfPoints() == 0:
        raise ValueError(
            "No point data could be loaded from '" + filenameSTL)
        return None
    
    return polydata


def main():
    colors = vtkNamedColors()

    filename, filetype = get_custom_parameters()

    reader = readfile(filename, filetype)

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d('Tan'))

    # Create a rendering window and renderer
    ren = vtkRenderer()
    renWin = vtkRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetWindowName('ReadVTP')

    # Create a renderwindowinteractor
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Assign actor to the renderer
    ren.AddActor(actor)

    # Enable user interface interactor
    iren.Initialize()
    renWin.Render()

    ren.SetBackground(colors.GetColor3d('AliceBlue'))
    ren.GetActiveCamera().SetPosition(-0.5, 0.1, 0.0)
    ren.GetActiveCamera().SetViewUp(0.1, 0.0, 1.0)
    renWin.Render()
    iren.Start()


if __name__ == '__main__':
    main()
