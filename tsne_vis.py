import numpy as np
import os, argparse
import tensorflow as tf
import matplotlib as mlp
import matplotlib.pyplot as plt
from PIL import Image
from lapjv import lapjv
from sklearn.manifold import TSNE
from scipy.spatial.distance import cdist
from tensorflow.python.keras.preprocessing import image
import pickle

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--size', type=int, help="Number of small images in a row/column in output image")
parser.add_argument('-d', '--dir',  type=str, help="Source directory for images")
parser.add_argument('-r', '--res',  type=int, default=224, help="Width/height of output square image")
parser.add_argument('-n', '--name', type=str, default='tsne_vis_output.jpg', help='Name of output image file')
parser.add_argument('-p', '--path', type=str, default='./', help="Destination directory for output image")
parser.add_argument('-x', '--per',  type=int, default=50, help="Tsne perplexity")
parser.add_argument('-i', '--iter', type=int, default=5000, help="Number of iterations in tsne algorithm")

args = parser.parse_args()
out_res = args.res
out_name = args.name
out_dim = args.size
to_plot = np.square(out_dim)
perplexity = args.per
tsne_iter = args.iter

if out_dim == 1:
    raise ValueError("Output grid dimension 1x1 not supported.")

if os.path.exists(args.dir):
    in_dir = args.dir
else:
    raise argparse.ArgumentTypeError("'{}' not a valid directory.".format(in_dir))
    
if os.path.exists(args.path):
    out_dir = args.path
else:
    raise argparse.ArgumentTypeError("'{}' not a valid directory.".format(out_dir))
    
def load_img(in_dir):
    pred_img = [f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))]
    img_collection = []
    for idx, img in enumerate(pred_img):
        img = os.path.join(in_dir, img)
        img_collection.append(image.load_img(img, target_size=(out_res, out_res)))
    if (np.square(out_dim) > len(img_collection)):
        raise ValueError("Cannot fit {} images in {}x{} grid".format(len(img_collection), out_dim, out_dim))
    return img_collection
    
def generate_tsne(activations):
    tsne = TSNE(perplexity=perplexity, n_components=2, init='random', n_iter=tsne_iter)
    X_2d = tsne.fit_transform(np.array(activations)[0:to_plot,:])
    X_2d -= X_2d.min(axis=0)
    X_2d /= X_2d.max(axis=0)
    return X_2d
    
def save_tsne_grid(img_collection, X_2d, out_res, out_dim):
    grid = np.dstack(np.meshgrid(np.linspace(0, 1, out_dim), np.linspace(0, 1, out_dim))).reshape(-1, 2)
    cost_matrix = cdist(grid, X_2d, "sqeuclidean").astype(np.float32)
    cost_matrix = cost_matrix * (100000 / cost_matrix.max())
    row_asses, col_asses, _ = lapjv(cost_matrix)
    grid_jv = grid[col_asses]
    out = np.ones((out_dim*out_res, out_dim*out_res, 3))
    
    for pos, img in zip(grid_jv, img_collection[0:to_plot]):
        h_range = int(np.floor(pos[0]* (out_dim - 1) * out_res))
        w_range = int(np.floor(pos[1]* (out_dim - 1) * out_res))
        out[h_range:h_range + out_res, w_range:w_range + out_res]  = image.img_to_array(img)
    
    im = image.array_to_img(out)
    im.save(out_dir + out_name, quality=100)
    
def main():
    img_collection = load_img(in_dir)
    activations=pickle.loads(open('get_activations_out', "rb").read())
    print("Generating 2D representation.")
    X_2d = generate_tsne(activations)
    print("Generating image grid.")
    save_tsne_grid(img_collection, X_2d, out_res, out_dim)

if __name__ == '__main__':
    main()
