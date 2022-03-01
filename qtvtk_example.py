"""
Simple test of Python QVTKRenderWindowInterator,
requires PyQt5.
"""

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer, vtkTextActor
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingFreeType

import vtkmodules.qt
vtkmodules.qt.QVTKRWIBase = "QGLWidget"
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import PyQt5

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QSurfaceFormat, QIcon, QPixmap
from PyQt5.QtOpenGL import QGLFormat
    
# elif PyQtImpl == "PySide2":
#     from PySide2.QtWidgets import QApplication
#     from PySide2.QtWidgets import QMainWindow
#     from PySide2.QtWidgets import QFrame
#     from PySide2.QtWidgets import QHBoxLayout
#     from PySide2.QtWebEngineWidgets import QWebEngineView
#     from PySide2.QtWebEngineWidgets import QWebEngineSettings
#     from PySide2.QtCore import Qt
#     from PySide2.QtCore import QUrl
#     from PySide2.QtCore import QCoreApplication
#     from PySide2.QtOpenGL import QGLFormat
# else:
#     raise ImportError("Unknown PyQt implementation " + repr(PyQtImpl))


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.frame = QFrame()
        self.frame_layout = QHBoxLayout()
        self.frame.setLayout(self.frame_layout)

        self.setCentralWidget(self.frame)

        self.create_webengine_widget()
        self.frame_layout.addWidget(self.view)

        self.create_vtk_widget()
        self.frame_layout.addWidget(self.vtk_widget)

        self.show()
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

        self.show_formats()

    def create_vtk_widget(self):
        print("Create vtk widget")
        # create the widget
        self.vtk_widget = QVTKRenderWindowInteractor(parent=self.frame)

        ren = vtkRenderer()
        ren.SetBackground(0, .1, .5)
        self.vtk_widget.GetRenderWindow().AddRenderer(ren)

        cone = vtkConeSource()
        cone.SetResolution(8)

        coneMapper = vtkPolyDataMapper()
        coneMapper.SetInputConnection(cone.GetOutputPort())

        coneActor = vtkActor()
        coneActor.SetMapper(coneMapper)

        ren.AddActor(coneActor)

    def create_webengine_widget(self):
        print("Create webengine widget")

        self.view = QWebEngineView(self.frame)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.view.settings().setAttribute(QWebEngineSettings.WebGLEnabled, False)
        self.view.settings().setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        self.view.load(QUrl("http://www.slate.fr/sites/default/files/styles/1200x680/public/capture_decran_2014-07-21_a_10.25.00.png"))
        
        # # self.view.load()
        # pixmap = QPixmap('project/fig/rtx001.png')
        # # label.setPixmap(pixmap)
        # self.view.resize(pixmap.width(),pixmap.height())

    def show_formats(self):
        print("Widget format")
        fmt = self.vtk_widget.format()
        print(fmt.profile())
        print("{}.{}".format(fmt.majorVersion(), fmt.minorVersion()))
        print("-----------------")
        print("QSurface format")
        fmt = QSurfaceFormat.defaultFormat()
        print(fmt.profile())
        print(fmt.renderableType())
        print("{}.{}".format(fmt.majorVersion(), fmt.minorVersion()))
        print("-----------------")
        print("QGLFormat")
        fmt = QGLFormat.defaultFormat()
        print(fmt.profile())
        print("{}.{}".format(fmt.majorVersion(), fmt.minorVersion()))
        print("-----------------")


if __name__ == "__main__":
    surfaceFormat = QGLFormat.defaultFormat()
    surfaceFormat.setProfile(QGLFormat.CoreProfile)
    surfaceFormat.setVersion(3, 3)
    surfaceFormat.setSamples(4)
    QGLFormat.setDefaultFormat(surfaceFormat)

    QCoreApplication.setOrganizationName("QtExamples")
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])
    window = MainWindow()

    # start event processing

    app.exec_()
