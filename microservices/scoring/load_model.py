import numpy as np
import torch
import mlflow.pytorch
from transformers import AutoTokenizer
import os

def load_model():  
    model_path = os.path.join(os.path.dirname(__file__), "model")
    model = mlflow.pytorch.load_model(
        model_uri=f"file://{model_path}",
        map_location=torch.device("cpu")
    )
    return model

# Define helper functions for tokenization
def get_ids_mask(sentences, tokenizer):
    max_length = 64
    tokenized = [tokenizer.tokenize(s) for s in sentences]
    tokenized = [t[:(max_length - 1)] + ['SEP'] for t in tokenized]

    ids = [tokenizer.convert_tokens_to_ids(t) for t in tokenized]
    ids = np.array([np.pad(i, (0, max_length - len(i)),
                           mode='constant') for i in ids])
    amasks = []
    for seq in ids:
        seq_mask = [float(i > 0) for i in seq]
        amasks.append(seq_mask)
    return ids, amasks

def load_process_sentences(sentences):
    sentences = ["[CLS] " + s for s in sentences]
    model_name = "bert-base-uncased" 
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    ids, amasks = get_ids_mask(sentences, tokenizer)
    inputs = torch.tensor(ids)
    masks = torch.tensor(amasks)
    return inputs, masks