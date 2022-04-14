import torch
from torch.utils.data import Dataset
import numpy as np

# gesture_database = [
#     ('test gesture 1', np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]])),
#     ('test gesture 2', np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]))
# ]


class GestureDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        angles = np.array(self.data[idx][1]).astype('float')
        sample = {'tag': self.data[idx][0], 'angles': angles}
        return sample
