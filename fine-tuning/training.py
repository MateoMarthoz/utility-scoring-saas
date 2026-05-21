import torch
import mlflow
import numpy as np
from utils import flatten, unflatten
import os

# Training and evaluation

def train(model, optimizer, train_dataloader, epoch, log_interval = 10):
    # Set model to training mode
    model.train()
    criterion = torch.nn.BCEWithLogitsLoss()
    ntrain_steps = len(train_dataloader)

    # Loop over each batch from the training set
    for step, batch in enumerate(train_dataloader):

        # Copy data to GPU if needed
        batch = tuple(t.cuda() for t in batch)

        # Unpack the inputs from our dataloader
        b_input_ids, b_input_mask, b_labels = batch

        # reshape
        b_input_ids = flatten(b_input_ids)
        b_input_mask = flatten(b_input_mask)

        # Zero gradient buffers
        optimizer.zero_grad()

        # Forward pass
        output = model(b_input_ids, attention_mask=b_input_mask)[0]  # dim 1
        output = unflatten(output)
        diffs = output[:, 0] - output[:, 1]
        loss = criterion(diffs.squeeze(dim=1), torch.ones(diffs.shape[0]).cuda())

        # Backward pass
        loss.backward()

        # Update weights
        optimizer.step()

        if step % log_interval == 0 and step > 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, step, ntrain_steps, 100. * step / ntrain_steps, loss)) 
            
            mlflow.log_metric("training_loss", loss.item(), step=(epoch * ntrain_steps + step))

def evaluate(model, dataloader):
    model.eval()
    cors = []

    for step, batch in enumerate(dataloader):
        # Copy data to GPU if needed
        batch = tuple(t.cuda() for t in batch)

        # Unpack the inputs from our dataloader
        b_input_ids, b_input_mask, b_labels = batch

        # reshape
        b_input_ids = flatten(b_input_ids)
        b_input_mask = flatten(b_input_mask)

        # Forward pass
        with torch.no_grad():
            output = model(b_input_ids, attention_mask=b_input_mask)[0]  # dim 1
            output = unflatten(output)
            diffs = output[:, 0] - output[:, 1]
            diffs = diffs.squeeze(dim=1).detach().cpu().numpy()
        cors.append(diffs > 0)

    cors = np.concatenate(cors)
    acc = np.mean(cors)

    print('Acc {:.3f}'.format(acc))
    return acc