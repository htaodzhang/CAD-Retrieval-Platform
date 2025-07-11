import os
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics.pairwise import euclidean_distances


def l2_normalize(features):
    features_c = features.copy()
    features_c /= np.sqrt((features_c * features_c).sum(axis=1))[:, None]
    return features_c


def compute_distance(x, y, l2=True):
    if l2:
        x = l2_normalize(x)
        y = l2_normalize(y)
    distances = euclidean_distances(x, y)
    min_distance = distances.min()
    max_distance = distances.max()
    if max_distance == min_distance:
        normalized_distances = np.zeros_like(distances)
    else:
        normalized_distances = (distances - min_distance) / (max_distance - min_distance)
    return normalized_distances


def computer_cos(x, y, l2=True):
    if l2:
        x = l2_normalize(x)
        y = l2_normalize(y)
    x_nor = F.normalize(torch.tensor(x), p=2, dim=1)
    y_nor = F.normalize(torch.tensor(y), p=2, dim=1)
    cos = 1 - torch.mm(x_nor, y_nor.t())
    return cos.numpy()


def generate_retrival_distance(x, y, l2=True, dis='euclidean'):
    if dis == 'euclidean':
        result = compute_distance(x, y, l2)
    elif dis == 'cos':
        result = computer_cos(x, y, l2)
    return result


def retrieval(x, y):
    result = generate_retrival_distance(x, y, l2=True, dis='euclidean')
    sorted_indices = np.argsort(result, axis=1)
    sorted = np.sort(result, axis=1)
    return sorted_indices, sorted


def get_file_paths(folder_path):
    file_paths = []
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item)
        if os.path.isfile(full_path) and (item.lower().endswith('.step') or item.lower().endswith('.stp')):
            file_paths.append(full_path)
    file_paths.sort()
    return file_paths


def load_features_from_folder(folder_path):
    features = []
    for item in os.listdir(folder_path):
        if item.endswith('.npy'):
            file_path = os.path.join(folder_path, item)
            feature = np.load(file_path, allow_pickle=True)
            features.append(feature)
    return np.vstack(features) if features else np.array([])


def process_query(x, database_input, folder_path, is_single_file=True):
    if is_single_file:
        y = database_input
    else:
        y = load_features_from_folder(database_input)

    if len(y) == 0:
        return [], []

    index, score = retrieval(x, y)
    retrieval_path = get_file_paths(folder_path)
    result_paths = []
    result_scores = []

    for i in range(len(retrieval_path)):
        path = retrieval_path[index[0][i]]
        result_paths.append(path)
        result_scores.append(float(score[0][i]))

    return result_paths, result_scores