import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data
from dataset import GestureDataset

learning_rate = 0.005
num_lables = 8


class NeuralNet(nn.Module):
    def __init__(self, lrate, loss_fn, in_size, out_size):
        super(NeuralNet, self).__init__()
        hidden_units_1 = 10
        hidden_units_2 = 8
        self.model = nn.Sequential(
            nn.Linear(in_size, hidden_units_1),
            nn.ReLU(),
            nn.Linear(hidden_units_1, hidden_units_2),
            nn.ReLU(),
            nn.Linear(hidden_units_2, out_size),
        )
        self.loss_fn = loss_fn
        self.optimizer = optim.SGD(self.model.parameters(), lr=lrate)

    def forward(self, x):
        return self.model(x)

    def step(self, x, y):
        pred_label = self.forward(x)
        loss = self.loss_fn(pred_label, y)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss


def fit(train_set, train_labels, dev_set, n_iter, batch_size=100):
    net = NeuralNet(learning_rate, nn.CrossEntropyLoss(), train_set.shape[1], num_lables)

    losses = np.empty(n_iter)
    for epoch in range(n_iter):
        batch_set = train_set.split(batch_size)
        batch_labels = train_labels.split(batch_size)
        for i in range(len(batch_set) - 1):
            net.step(batch_set[i], batch_labels[i])
        losses[epoch] = net.step(batch_set[-1], batch_labels[-1])

    yhats = torch.argmax(net.forward(dev_set), dim=1).tolist()

    return losses, yhats, net


def compute_accuracies(predicted_labels, dev_set, dev_labels):
    yhats = predicted_labels
    if len(yhats) != len(dev_labels):
        print("Lengths of predicted labels don't match length of actual labels", len(yhats), len(dev_labels))
        return 0., 0., 0., 0.

    accuracy = np.mean(yhats == dev_labels)

    tp = np.sum([yhats[i] == dev_labels[i] and yhats[i] == 1 for i in range(len(dev_labels))])
    fp = np.sum([yhats[i] != dev_labels[i] and yhats[i] == 1 for i in range(len(dev_labels))])
    fn = np.sum([yhats[i] != dev_labels[i] and yhats[i] == 0 for i in range(len(dev_labels))])

    precision = tp / (tp + fp)
    recall = tp / (fn + tp)
    f1 = 2 * (precision * recall) / (precision + recall)

    return accuracy, f1, precision, recall


def load_json():
    return list()


def load_dataset():
    dataset = GestureDataset
    X = A['data']
    Y = A['label']

    data.random_split(dataset, [len(dataset)])

    # animals = [2, 3, 4, 5, 6, 7]
    # Y = np.array([float(Y[i] in animals) for i in range(len(Y))])
    # Y_test = np.array([float(Y_test[i] in animals) for i in range(len(Y_test))])

    return X, Y, X_test, Y_test


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Neural Method')
    parser.add_argument('--lrate', type=float, help='learning rate')
    parser.add_argument('--max_iter', types=int, help='maximum iterations')
