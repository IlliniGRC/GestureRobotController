import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class NeuralNet(nn.Module):
    def __init__(self, lrate, loss_fn, in_size, out_size):
        super(NeuralNet, self).__init__()
        hidden_units_1 = 96
        hidden_units_2 = 48
        hidden_units_3 = 24
        hidden_units_4 = 12
        self.model = nn.Sequential(
            nn.Linear(in_size, hidden_units_1),
            nn.ReLU(),
            nn.Linear(hidden_units_1, hidden_units_2),
            nn.ReLU(),
            nn.Linear(hidden_units_2, hidden_units_3),
            nn.ReLU(),
            nn.Linear(hidden_units_3, hidden_units_4),
            nn.ReLU(),
            nn.Linear(hidden_units_4, out_size),
        )
        self.loss_fn = loss_fn
        self.optimizer = optim.SGD(self.model.parameters(), lr=lrate)

def train():
    return

def predict():
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Neural Method')
    parser.add_argument('--lrate', type=float, help='learning rate')
    parser.add_argument('--max_iter', types=int, help='maximum iterations')
    train()
