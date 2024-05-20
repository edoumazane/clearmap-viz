#!/usr/bin/env python3

__author__ = "Etienne Doumazane"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Etienne Doumazane"
__email__ = "etienne.doumazane@icm-institute.org"
__status__ = "Development"

"""
This module contains utils to visualize images in the napari viewer and interact with it.
"""

from pathlib import Path
import numpy as np
import napari
from clearmap_viz.data import load_img
from clearmap_viz.utils import timestamp_error, timestamp_info, timestamp_ok, timestamp_warning

#####################################################
### Open a file or an array-like object in napari ###
#####################################################

def view_img(source, viewer=None, slicing=(slice(None),slice(None),slice(None)), **kwargs):
    """
    View a 3D image in napari.
    input:
        source: str or Path - path to the image file or array-like
        viewer: napari.Viewer - napari viewer to which the image should be added - if None, create a new viewer
        slicing: tuple of 3 slices - slicing of the image to be displayed
        translate: bool - if True, the slicing is used to translate the image in the viewer
        kwargs: additional arguments for napari.Viewer.add_image
    """
    if viewer is None:
        viewer = napari.current_viewer()
        if viewer is None:
            viewer = napari.Viewer()
    if isinstance(source, (str, Path)):
        source = load_img(source)
    if kwargs.get("translate") == True:
        kwargs["translate"] = list(s.start for s in slicing)
    viewer.add_image(source[slicing], **kwargs)
    return viewer

def view_labels(source, viewer=None, slicing=(slice(None),slice(None),slice(None)), **kwargs):
    """
    View a 3D label image in napari.
    input:
        source: str or Path - path to the image file or array-like
        viewer: napari.Viewer - napari viewer to which the image should be added - if None, create a new viewer
        slicing: tuple of 3 slices - slicing of the image to be displayed
        translate: bool - if True, the slicing is used to translate the image in the viewer
        kwargs: additional arguments for napari.Viewer.add_labels
    """
    if viewer is None:
        viewer = napari.current_viewer()
        if viewer is None:
            viewer = napari.Viewer()
    if isinstance(source, (str, Path)):
        source = load_img(source)
    if kwargs.get("translate") == True:
        kwargs["translate"] = list(s.start for s in slicing)
    viewer.add_labels(source[slicing], **kwargs)
    return viewer

def view_points(source, viewer=None, slicing=(slice(None),slice(None),slice(None)), **kwargs):
    """
    View points in napari.
    input:
        source: str or Path - path to the coordinates file or array-like
        viewer: napari.Viewer - napari viewer to which the points should be added - if None, create a new viewer
        slicing: tuple of 3 slices - slicing of the points to be displayed
        translate: bool - if True, the slicing is used to translate the points in the viewer
        kwargs: additional arguments for napari.Viewer.add_points
    """
    if viewer is None:
        viewer = napari.current_viewer()
        if viewer is None:
            viewer = napari.Viewer()
    # if isinstance(source, (str, Path)):
    #     source = np.load(source)
    # if kwargs.get("translate") == True:
    #     kwargs["translate"] = list(s.start for s in slicing)
    viewer.add_points(source, **kwargs)
    return viewer

########################################################
### Utils to convert between slicing and coordinates ###
########################################################

def convert_slicing_to_center(slicing):
    """
    Convert a slicing to an array of coordinates that define the center and an array of dimensions.
    example
        input: (slice(100,200), slice(300,400), slice(500,600))
        output: np.array([150, 350, 550]), np.array([100, 100, 100])
    """
    center = np.array([s.start + (s.stop - s.start)//2 for s in slicing])
    dimensions = np.array([(s.stop - s.start) for s in slicing])
    return center, dimensions

def convert_center_to_slicing(coords_center, dimensions, reverse_order=False):
    """
    Convert a center coordinate and dimensions to a slicing.
    If reverse_order is True, the slicing is returned in the reverse order.
    example
        input: np.array([150, 350, 550]), np.array([100, 100, 100])
        output: (slice(100,200), slice(300,400), slice(500,600))
    """
    dimensions = np.array(dimensions).astype(int)
    coords_center = np.array(coords_center).astype(int)
    half_dimensions = np.array(dimensions) // 2
    coords_min = coords_center - half_dimensions
    coords_max = coords_center - half_dimensions + dimensions
    slicing = tuple([slice(min_, max_) for min_, max_ in zip(coords_min, coords_max)])
    if reverse_order:
        return slicing[::-1]
    return slicing


##################################################
### Utils to add scalebar and take screenshots ###
##################################################

def takescreenshot(viewer=None, save=None, size=None, **kwargs):
    """
    Take and display the screenshot of the viewer
    """
    import matplotlib.pyplot as plt
    viewer = viewer or napari.current_viewer()
    plt.imshow(viewer.screenshot())
    plt.axis('off')
    if save is not None:
        plt.savefig(save, **kwargs)
    return plt.show()



##############################################
### Utils to get and set camera parameters ###
##############################################

def get_camera_params(viewer=None):
    """
    Get the current camera parameters.
    What is printed can be copy-pasted in a script to reproduce the current view (2D).
    """
    viewer = viewer or napari.current_viewer()
    center = tuple(np.array(viewer.camera.center).astype(int))
    zoom = viewer.camera.zoom.round(2)
    print(f"""viewer.camera.center = {center}\nviewer.camera.zoom = {zoom}\nviewer.dims.set_current_step(0, {viewer.dims.current_step[0]})""")
    return center, zoom, viewer.dims.current_step[0]

def go_to_slice(z, viewer=None):
    """
    Go to the given slice in the current viewer.
    z: int - slice number
    """
    viewer = viewer or napari.current_viewer()
    viewer.dims.set_current_step(0, z)

def get_layers_params(viewer=None):
    viewer = viewer or napari.current_viewer()
    dict_params = {}
    for layer in napari.current_viewer().layers:
        dict_params[layer.name] = dict(visible=layer.visible,
                                    opacity=layer.opacity,
                                    contrast_limits=layer.contrast_limits,
                                    gamma=layer.gamma,
                                    colormap__name=layer.colormap.name,
                                    blending=layer.blending,
                                    rendering=layer.rendering,
                                    attenuation=layer.attenuation,)
    return dict_params

def set_layers_params(dict_params, viewer=None):
    viewer = viewer or napari.current_viewer()
    for layer_name, layer_params in dict_params.items():
        layer = napari.current_viewer().layers[layer_name]
        if not layer.visible:
            timestamp_warning(f"Layer {layer_name} ignored because it is not visible")
        else:
            for param_name, param_value in layer_params.items():
                try:
                    setattr(layer, param_name, param_value)
                except:
                    print(f"Could not set {param_name} for layer {layer_name}")



#####################################
### Utils to get points or labels ###
#####################################

def get_points(layer_name="Points", viewer=None):
    """
    Get the coordinates of the points a Points layer.
    points_layer: str - name of the Points layer.
    returns an array of ZYX coordinates
    """
    viewer = viewer or napari.current_viewer()
    return viewer.layers[layer_name].data.round().astype(int)

def get_labels(layer_name="Labels", viewer=None):
    """
    Get the labels from a Labels layer.
    labels_layer: str - name of the Labels layer.
    returns a 3D array of labels (int).
    """
    viewer = viewer or napari.current_viewer()
    return viewer.layers[layer_name].data

def get_shapes(layer_name="Shapes", viewer=None):
    """
    Get the labels from a Labels layer.
    labels_layer: str - name of the Labels layer.
    returns a 3D array of labels (int).
    """
    viewer = viewer or napari.current_viewer()
    return viewer.layers[layer_name].data
