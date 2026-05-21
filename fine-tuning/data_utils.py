import torch
import numpy as np
from torch.utils.data import TensorDataset
from transformers import AutoTokenizer
from datasets import load_dataset

# Data loading and preprocessing

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def get_ids_mask(sentences):
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

def load_sentences(split="train"):
    dataset = load_dataset("metaeval/utilitarianism", split=split)

    # Create a list of sentences
    sentences = []
    for better, worse in zip(dataset['better_choice'], dataset['worst_choice']):
        sentences.append(better) 
        sentences.append(worse)  

    # Create a list of dummy labels (since labels are not used in this case)
    labels = [-1 for _ in range(len(sentences))]

    return sentences, labels


def load_process_data(split="train"):
    sentences, labels = load_sentences(split=split)
    sentences = ["[CLS] " + s for s in sentences]
    ids, amasks = get_ids_mask(sentences)
    inputs, labels, masks = torch.tensor(ids), torch.tensor(labels), torch.tensor(amasks)

    even_mask = [i for i in range(inputs.shape[0]) if i % 2 == 0]
    odd_mask = [i for i in range(inputs.shape[0]) if i % 2 == 1]
    even_inputs, odd_inputs = inputs[even_mask], inputs[odd_mask]
    even_labels, odd_labels = labels[even_mask], labels[odd_mask]
    even_masks, odd_masks = masks[even_mask], masks[odd_mask]
    inputs = torch.stack([even_inputs, odd_inputs], axis=1)
    labels = torch.stack([even_labels, odd_labels], axis=1)
    masks = torch.stack([even_masks, odd_masks], axis=1)

    data = TensorDataset(inputs, masks, labels)
    return data