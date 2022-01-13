# trace generated using paraview version 5.8.0
#
# To ensure correct image size when batch processing, please search 
# for and uncomment the line `# renderView*.ViewSize = [*,*]`

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new 'Legacy VTK Reader'
fire2coonspatchgridvtk = LegacyVTKReader(FileNames=['/work/dgd/examples/geom/grids/fire2-coons-patch-grid.vtk'])

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')
# uncomment following to set a specific view size
# renderView1.ViewSize = [2847, 1171]

# get layout
layout1 = GetLayout()

# show data in view
fire2coonspatchgridvtkDisplay = Show(fire2coonspatchgridvtk, renderView1, 'StructuredGridRepresentation')

# trace defaults for the display properties.
fire2coonspatchgridvtkDisplay.Representation = 'Surface'
fire2coonspatchgridvtkDisplay.ColorArrayName = [None, '']
fire2coonspatchgridvtkDisplay.OSPRayScaleFunction = 'PiecewiseFunction'
fire2coonspatchgridvtkDisplay.SelectOrientationVectors = 'None'
fire2coonspatchgridvtkDisplay.ScaleFactor = 0.045406922698020935
fire2coonspatchgridvtkDisplay.SelectScaleArray = 'None'
fire2coonspatchgridvtkDisplay.GlyphType = 'Arrow'
fire2coonspatchgridvtkDisplay.GlyphTableIndexArray = 'None'
fire2coonspatchgridvtkDisplay.GaussianRadius = 0.002270346134901047
fire2coonspatchgridvtkDisplay.SetScaleArray = [None, '']
fire2coonspatchgridvtkDisplay.ScaleTransferFunction = 'PiecewiseFunction'
fire2coonspatchgridvtkDisplay.OpacityArray = [None, '']
fire2coonspatchgridvtkDisplay.OpacityTransferFunction = 'PiecewiseFunction'
fire2coonspatchgridvtkDisplay.DataAxesGrid = 'GridAxesRepresentation'
fire2coonspatchgridvtkDisplay.PolarAxes = 'PolarAxesRepresentation'
fire2coonspatchgridvtkDisplay.ScalarOpacityUnitDistance = 0.05481861671452429

# reset view to fit data
renderView1.ResetCamera()

#changing interaction mode based on data extents
renderView1.InteractionMode = '2D'
renderView1.CameraPosition = [0.03642173111438751, 0.22703461349010468, 10000.0]
renderView1.CameraFocalPoint = [0.03642173111438751, 0.22703461349010468, 0.0]

# get the material library
materialLibrary1 = GetMaterialLibrary()

# update the view to ensure updated data information
renderView1.Update()

# change representation type
fire2coonspatchgridvtkDisplay.SetRepresentationType('Outline')

# get animation scene
animationScene1 = GetAnimationScene()

animationScene1.GoToLast()

# change solid color
fire2coonspatchgridvtkDisplay.AmbientColor = [0.0, 0.3333333333333333, 1.0]
fire2coonspatchgridvtkDisplay.DiffuseColor = [0.0, 0.3333333333333333, 1.0]

# Properties modified on fire2coonspatchgridvtkDisplay
fire2coonspatchgridvtkDisplay.LineWidth = 3.0

# Properties modified on fire2coonspatchgridvtkDisplay
fire2coonspatchgridvtkDisplay.LineWidth = 4.0

# Hide orientation axes
renderView1.OrientationAxesVisibility = 0

# current camera placement for renderView1
renderView1.InteractionMode = '2D'
renderView1.CameraPosition = [0.03642173111438751, 0.22703461349010468, 10000.0]
renderView1.CameraFocalPoint = [0.03642173111438751, 0.22703461349010468, 0.0]
renderView1.CameraParallelScale = 0.24173495193661831

# save screenshot
SaveScreenshot('/work/dgd/examples/geom/grids/fire2-domain.png', renderView1, ImageResolution=[2847, 1171],
    TransparentBackground=1)

#### saving camera placements for all active views

# current camera placement for renderView1
renderView1.InteractionMode = '2D'
renderView1.CameraPosition = [0.03642173111438751, 0.22703461349010468, 10000.0]
renderView1.CameraFocalPoint = [0.03642173111438751, 0.22703461349010468, 0.0]
renderView1.CameraParallelScale = 0.24173495193661831

#### uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).