from .params import LOCAL_CLEARMAP, __file__ as params_file
from .utils import timestamp_error, timestamp_info, timestamp_ok, timestamp_warning
import sys
from pathlib import Path
import pandas as pd
from .graph_viz import plot_components, plot_radii, plot_components, plot_radii, plot_degrees, plot_edge_value

try:
    import ClearMap.Analysis.Graphs.GraphGt as ggt
except ImportError:
    import sys
    timestamp_warning("ClearMap not accessible. Appending ClearMap local path.")
    if str(LOCAL_CLEARMAP) not in sys.path:
        sys.path.append(str(LOCAL_CLEARMAP))
    try:
        import ClearMap.Analysis.Graphs.GraphGt as ggt
        timestamp_ok(f"ClearMap is now accessed from {LOCAL_CLEARMAP}.")
    except Exception as e:
        timestamp_warning(f"Could not import ClearMap. You may want to install it on env or write ClearMap's path in module {params_file}. {e}")
        load_graph = lambda x: timestamp_error("Cannot load_graph. ClearMap not accessible.")


def load_graph(fpath):
    """
    Load a graph from a file.
    """
    fpath = str(fpath)
    g = ggt.load(fpath)
    return Graph(g)


class Graph(ggt.Graph):
    def __init__(self, ggt_graph):
        self.__dict__ = ggt_graph.__dict__.copy()

    def compute_dfs(self, with_eg_df=False):
        """
        Return a dataframe of vertices and a dataframe of edges
        """

        # creates a vertex dataframe
        self.v_df = pd.DataFrame()
        self.v_df[["x", "y", "z"]] = self.vertex_coordinates()
        self.v_df["degree"] = self.vertex_degrees()
        self.v_df["component"] = self.label_components()


        # creates an edge dataframe
        self.e_df = pd.DataFrame()
        self.e_df[["starting_vertex", "ending_vertex"]] = self.edge_connectivity()
        self.e_df["component"] = self.v_df.loc[self.e_df["starting_vertex"], "component"].values
        self.e_df["starting_degree"] = self.v_df.loc[self.e_df["starting_vertex"], "degree"].values
        self.e_df["ending_degree"] = self.v_df.loc[self.e_df["ending_vertex"], "degree"].values
        self.e_df[["starting_x", "starting_y", "starting_z"]] = self.v_df.loc[self.e_df["starting_vertex"], ["x", "y", "z"]].values
        self.e_df[["ending_x", "ending_y", "ending_z"]] = self.v_df.loc[self.e_df["ending_vertex"], ["x", "y", "z"]].values

        # creates an edge_geometry dataframe
        if with_eg_df:
            self.eg_df = pd.DataFrame(self.graph_property("edge_geometry_coordinates"), columns=["x", "y", "z"])
            self.eg_df["radii"] = self.graph_property("edge_geometry_radii")
            self.eg_df["edge_index"] = -1
            # this takes time
            for i, (start, finish) in enumerate(self.edge_geometry_indices().tolist()):
                self.eg_df.loc[start:finish, "edge_index"] = i

        # adds edge_properties
        self.e_df["radius"] = self.edge_property("radii")
        self.e_df["length"] = self.edge_property("length")


        # adds topology properties of the edges
        self.e_df["has_degree_2"] = (self.e_df[["starting_degree", "ending_degree"]] == 2).any(axis=1)
        self.e_df["min_degree"] = self.e_df[["starting_degree", "ending_degree"]].min(axis=1)
        self.e_df["is_self_loop"] = self.e_df["starting_vertex"] == self.e_df["ending_vertex"]

        # adds connected_edges to df vertices
        df_vertex_connectivity = pd.concat([self.e_df["starting_vertex"], self.e_df["ending_vertex"]], axis=0).to_frame(name="vertex_index").reset_index(names="edge_index")
        self.v_df = self.v_df.join(df_vertex_connectivity.groupby("vertex_index").agg(list).rename(columns={"edge_index": "connected_edges"}))




        for prop in self.vertex_properties:
            self.v_df["vp_" + prop] = list(self.vertex_property(prop))

        for prop in self.edge_properties:
            self.e_df["ep_" + prop] = list(self.edge_property(prop))

        return self

    def plot_radii(self):
        return plot_radii(self)

    def plot_components(self):
        return plot_components(self)

    def plot_degrees(self):
        return plot_degrees(self)

    def plot_edge_value(self, *args, **kwargs):
        return plot_edge_value(self, *args, **kwargs)
