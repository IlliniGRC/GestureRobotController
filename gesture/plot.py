# %%
import matplotlib.pyplot as plt
import numpy as np

with open("database.bin", "r") as f:
  content = f.read()

fig, axs = plt.subplots(2)
to_plot = [[] for _ in range(5)]
lines = content.split("\n")
for line in lines[:-1]:
  preprocess = line.split(",")
  for i, data in enumerate(preprocess):
    to_plot[i].append(float(data))

for i in range(4):
  axs[0].plot(range(len(to_plot[i])), to_plot[i])
axs[0].plot(range(0, len(to_plot[0]), 8), [4 for _ in range(0, len(to_plot[0]), 8)], ".")
axs[0].legend(["Gesture 0", "Gesture 1", "Gesture 2", 
    "Gesture 3", "Threshold"], loc=(1.04, 0.15))
axs[0].set_yticks(np.arange(0, 30, 5))
axs[0].set_ylabel("L2 Error")
axs[0].set_title("L2 error when doing different gestures")

axs[1].plot(range(len(to_plot[4])), to_plot[4])
axs[1].legend(["Prediction"], loc=(1.04, 0.4))
axs[1].set_xlabel("Sample")
axs[1].set_ylabel("Prediction")
axs[1].set_yticks(np.arange(-1, 4, 1))

plt.show()
