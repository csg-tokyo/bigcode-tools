import argparse

import pandas as pd
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objs as go
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


DEFAULT_CLUSTERS_COUNT = 6
DEFAULT_MAX_CLUSTERS = 10

SVG_COLORS = [
    "#1f77b4",  # muted blue
    "#ff7f0e",  # safety orange
    "#2ca02c",  # cooked asparagus green
    "#d62728",  # brick red
    "#9467bd",  # muted purple
    "#8c564b",  # chestnut brown
    "#e377c2",  # raspberry yogurt pink
    "#7f7f7f",  # middle gray
    "#bcbd22",  # curry yellow-green
    "#17becf",  # blue-teal
]


def memoize(f):
    memoized = {}
    def wrapper(*args):
        tupled_args = tuple(args)
        if tupled_args not in memoized:
            memoized[tupled_args] = f(*args)
        return memoized[tupled_args]
    return wrapper


@memoize
def load_model(model_path):
    metadata_path = model_path + ".meta"
    saver = tf.train.import_meta_graph(metadata_path)
    sess = tf.Session()
    saver.restore(sess, model_path)
    return sess


def load_embeddings(model_path):
    sess = load_model(model_path)
    return sess.run(sess.graph.get_tensor_by_name("embeddings:0"))


def load_labels(labels_path):
    return pd.read_csv(labels_path, sep="\t")


def sanitize_data(embeddings, labels):
    norms = np.linalg.norm(embeddings, axis=1)
    valid_indexes = np.abs(norms - np.mean(norms)) <= (np.std(norms) * 2)
    sanitized_embeddings = embeddings[valid_indexes]
    sanitized_labels = labels.iloc[labels.index[valid_indexes]].reset_index(drop=True)
    return (sanitized_embeddings, sanitized_labels)


def create_elbow_graph(embeddings, max_clusters=DEFAULT_MAX_CLUSTERS, output=None):
    scores = [KMeans(n_clusters=i).fit(embeddings).score(embeddings)
              for i in range(1, max_clusters)]
    plt.plot(list(range(1, max_clusters)), scores)
    if output:
        plt.savefig(output)
    else:
        plt.show()


def reduce_dimensions(embeddings, dimensions=2):
    pca = PCA(n_components=dimensions)
    return pca.fit_transform(embeddings)


def assign_clusters(embeddings, labels, clusters_count=DEFAULT_CLUSTERS_COUNT):
    clusters = KMeans(n_clusters=clusters_count, max_iter=30000).fit_predict(embeddings)
    labels["Cluster"] = clusters


def compute_clusters_count(labels):
    return labels.Cluster.max()


def create_scatter_plot(embeddings_2d, labels, output=None):
    clusters_count = compute_clusters_count(labels)

    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111)
    for i in range(clusters_count):
        indexes = labels[labels.Cluster == i].index.values
        ax.scatter(embeddings_2d[indexes, 0], embeddings_2d[indexes, 1], c=f"C{i}")
        for j in indexes:
            ax.annotate(labels.loc[j].Name, (embeddings_2d[j, 0], embeddings_2d[j, 1]), fontsize=8)

    if output:
        fig.savefig(output)
    else:
        plt.show()


def create_interactive_scatter_plot(embeddings_2d, labels, output=None):
    clusters_count = compute_clusters_count(labels)
    data = []
    for i in range(clusters_count):
        indexes = labels[labels.Cluster == i].index.values
        trace = go.Scatter(
            x=embeddings_2d[indexes, 0],
            y=embeddings_2d[indexes, 1],
            mode="markers",
            text=labels.loc[indexes].Name.values,
            marker={"color": SVG_COLORS[i]}
        )
        data.append(trace)

    kwargs = {"filename": output} if output else {}
    plotly.offline.plot(data, **kwargs)


def visualize_clusters(options):
    labels = load_labels(options.labels_path)
    embeddings = load_embeddings(options.model_path)
    embeddings, labels = sanitize_data(embeddings, labels)
    assign_clusters(embeddings, labels, options.clusters_count)
    embeddings_2d = reduce_dimensions(embeddings)
    if options.interactive:
        create_interactive_scatter_plot(embeddings_2d, labels, options.output)
    else:
        create_scatter_plot(embeddings_2d, labels, options.output)


def visualize_elbow_graph(options):
    embeddings = load_embeddings(options.model_path)
    create_elbow_graph(embeddings, max_clusters=options.max_clusters, output=options.output)


def create_visualize_clusters_parser(subparsers):
    parser = subparsers.add_parser("visualize-clusters", help="displays the clustered data in 2D")
    parser.add_argument(
        "-m", "--model-path", required=True, help="path of the trained model")
    parser.add_argument(
        "-l", "--labels-path", required=True, help="path of the vocabulary labels")
    parser.add_argument(
        "-i", "--interactive", default=False, action="store_true", help="uses interactive plot")
    parser.add_argument(
        "-n", "--clusters-count", default=DEFAULT_CLUSTERS_COUNT, type=int,
        help="number of clusters")
    parser.add_argument(
        "-o", "--output", default=None, help="the file to output the plot")


def create_elbow_graph_parser(subparsers):
    parser = subparsers.add_parser("elbow-graph", help="displays the clustered data in 2D")
    parser.add_argument(
        "-m", "--model-path", required=True, help="path of the trained model")
    parser.add_argument(
        "-o", "--output", default=None, help="the file to output the plot")
    parser.add_argument(
        "--max-clusters", default=DEFAULT_MAX_CLUSTERS, type=int,
        help="the maximum number of clusters to try")


def create_parser():
    parser = argparse.ArgumentParser(prog="data-explorer",
                                     description="help exploring learned data")

    subparsers = parser.add_subparsers(dest="command")
    create_visualize_clusters_parser(subparsers)
    create_elbow_graph_parser(subparsers)

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    if not args.command:
        parser.error("no command provided")
    elif args.command == "visualize-clusters":
        visualize_clusters(args)
    elif args.command == "elbow-graph":
        visualize_elbow_graph(args)


if __name__ == '__main__':
    main()
