import torch

# Utility functions

def flatten(tensor):
    return torch.cat([tensor[:, 0], tensor[:, 1]])

def unflatten(tensor):
    return torch.stack([tensor[:len(tensor) // 2], tensor[len(tensor) // 2:]], axis=1)