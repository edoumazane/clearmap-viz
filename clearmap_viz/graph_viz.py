from .utils import timestamp_error, timestamp_info, timestamp_ok, timestamp_warning
from matplotlib.colors import hsv_to_rgb
try:
    import pyvista as pv
except ImportError:
    timestamp_warning("Could not import pyvista.")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import graph_tool.all as gt
from pathlib import Path

from .data import load_img
from .params import LOCAL_CLEARMAP
# from .graph_utils import Graph


try:
    import ClearMap.Analysis.Graphs.GraphRendering as gr
except ImportError:
    import sys
    timestamp_info("ClearMap not accessible. Appending ClearMap local path.")
    if str(LOCAL_CLEARMAP) not in sys.path:
        sys.path.append(str(LOCAL_CLEARMAP))
    try:
        import ClearMap.Analysis.Graphs.GraphRendering as gr
    except Exception as e:
        timestamp_warning(f"Could not import ClearMap. Make sure it is installed and accessible from the current environment. {e}")
        load_graph = None


def make_rainbow_array(n_colors):
    """
    Return a (n_colors,3) array of rainbow colors in RGB (first is RED)
    That array can be used to define edge_colors or vertex_colors in the TubeMap viewer.
    Examples:
        components = graph.label_components()
        rainbow_colors = make_rainbow_array(n_colors)
        plot_graph_mesh(graph, vertex_colors=rainbow_colors[components % n_colors])
    """
    return hsv_to_rgb(np.array([np.linspace(0,1,n_colors, endpoint=False)] + 2*[np.ones(n_colors)]).T)

def digitize_bins(variable, n_bins, plot=True):
    """
    Return a vector of same size as variable, with values ranging from 0 to n_bins-1
    All values are equally
    """
    bins = np.quantile(variable[~np.isnan(variable)], np.linspace(0,1,n_bins))
    print(f"{len(bins)} bins with limits: ", " - ".join(map("{:.1e}".format, bins)))
    digitized = np.digitize(variable, bins=bins)-1
    if plot:
        fig, axs = plt.subplots(1,3, figsize=(15,3))
        axi = axs.flat
        plt.sca(next(axi))
        sns.histplot(variable, bins=100)
        for bin in bins:
            plt.axvline(bin, color="r")
        plt.sca(next(axi))
        sns.histplot(variable, bins=100)
        for bin in bins:
            plt.axvline(bin, color="r")
        plt.xscale("log")
        plt.yscale("log")
        plt.sca(next(axi))
        plot_discrete_distribution(digitized, log_y=False)
        plt.xlabel("Bins")
        plt.tight_layout()
    return digitized

def plot_discrete_distribution(variable, variable_name="", starts_at_zero=True, log_y=True):
    sns.histplot(variable, discrete=True)
    if log_y:
        plt.yscale("log")
    plt.xticks(np.arange(1-int(starts_at_zero), variable.max()+1, step=np.floor(variable.max()//12+1)))
    plt.xlabel(variable_name)

def plot_pyvista(g, edge_colors):
    if g.n_edges != len(edge_colors):
        raise ValueError(f"graph has {g.n_edges} edges, but {len(edge_colors)} colors were provided.")
    interpolation = gr.interpolate_edge_geometry(g, smooth=5, order=2, points_per_pixel=0.2, verbose=False)

    coordinates, faces, colors = gr.mesh_tube_from_coordinates_and_radii(*interpolation,
                                        n_tube_points=5, edge_colors=edge_colors,
                                        processes=None, verbose=False)

    n_faces = faces.shape[0]
    pv_faces = np.insert(faces, 0, 3, axis=1).flatten()

    mesh = pv.PolyData(coordinates, pv_faces, n_faces=n_faces)
    mesh.point_data['colors'] = colors

    return mesh.plot(smooth_shading=True, scalars='colors', rgb=True, return_viewer=True)


def plot_radii(graph):
    if not hasattr(graph, "e_df"):
        graph = graph.compute_dfs()
    digitized = digitize_bins(variable=graph.e_df["radius"], n_bins=24)
    rainbow_colors = make_rainbow_array(32)
    edge_colors = rainbow_colors[digitized]
    return plot_pyvista(graph, edge_colors)

def plot_degrees(graph):
    # degrees are clipped to a max value of 5
    if not hasattr(graph, "e_df"):
        graph = graph.compute_dfs()
    edge_min_degree = np.clip(graph.e_df["min_degree"].values, 0, 5)

    rainbow_colors = make_rainbow_array(6)
    edge_colors = rainbow_colors[edge_min_degree-1]
    return plot_pyvista(graph, edge_colors)

def plot_components(graph):
    # We limit the number of colors to 24
    if not hasattr(graph, "e_df"):
        graph = graph.compute_dfs()
    edge_components = graph.e_df["component"] % 24
    rainbow_colors = make_rainbow_array(24)
    edge_colors = rainbow_colors[edge_components]
    return plot_pyvista(graph, edge_colors)

def plot_edge_value(graph, column_name, n_bins=12, n_colors=24, digitize=True):
    if digitize:
        digitized = digitize_bins(variable=graph.e_df[column_name], n_bins=n_bins)
    else:
        digitized = graph.e_df[column_name]
    rainbow_colors = make_rainbow_array(n_colors)
    edge_colors = rainbow_colors[digitized]
    return plot_pyvista(graph, edge_colors)

def annotate_graph(graph, annotation, sampling_interval_graph, sampling_interval_annotation, annotation_name="annotation"):
    if isinstance(annotation, (str, Path)):
        annotation = load_img(annotation, swapaxes=False, as_dask_array=False)
    sampling_interval_graph = np.array(sampling_interval_graph)
    sampling_interval_annotation = np.array(sampling_interval_annotation)
    annotation_shape = np.array(annotation.shape)
    # TODO: check that the annotation and the graph have the same shape
    graph.v_df[annotation_name] = annotation[tuple(np.clip(np.round(graph.vertex_coordinates() * sampling_interval_graph / sampling_interval_annotation).astype(int), 0, annotation_shape - 1).T)]
    return graph

def transfer_v_to_e_property(graph, property_name, method="starting_vertex"):
    if method == "starting_vertex":
        graph.e_df[property_name] = graph.v_df.loc[graph.e_df["starting_vertex"], property_name].values
        return graph
    elif method == "ending_vertex":
        graph.e_df[property_name] = graph.v_df.loc[graph.e_df["ending_vertex"], property_name].values
        return graph
    elif method == "mean":
        graph.e_df[property_name] = graph.v_df.loc[graph.e_df[["starting_vertex", "ending_vertex"]].values.flatten(), property_name].values.reshape(-1, 2).mean(axis=1)
        return graph
    elif method == "max":
        graph.e_df[property_name] = graph.v_df.loc[graph.e_df[["starting_vertex", "ending_vertex"]].values.flatten(), property_name].values.reshape(-1, 2).max(axis=1)
        return graph
    elif method == "min":
        graph.e_df[property_name] = graph.v_df.loc[graph.e_df[["starting_vertex", "ending_vertex"]].values.flatten(), property_name].values.reshape(-1, 2).min(axis=1)
        return graph
    else:
        raise ValueError(f"method {method} not recognized")
