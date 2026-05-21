import torch
from transformers import AutoModelForSequenceClassification, AutoConfig, AdamW

# Model loading and optimizer setup

def load_model(args):
    # Load model configuration
    model_name = "bert-base-uncased"
    config = AutoConfig.from_pretrained(model_name, num_labels=1)
    
    # Initialize model
    model = AutoModelForSequenceClassification.from_pretrained(model_name, config=config)
    
    # Check available GPUs
    available_gpus = torch.cuda.device_count()
    if available_gpus > 0:
        model.cuda()
    else:
        print("No GPUs available, using CPU.")
        model.to(torch.device("cpu"))
    
    print(f'\nPretrained model "{model_name}" loaded')

    # Set up optimizer
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in model.named_parameters()
                    if not any(nd in n for nd in no_decay)],
         'weight_decay': 0.01},
        {'params': [p for n, p in model.named_parameters()
                    if any(nd in n for nd in no_decay)],
         'weight_decay': 0.0}
    ]
    learning_rate = float(args.learning_rate)
    optimizer = AdamW(optimizer_grouped_parameters, lr=learning_rate, eps=1e-8)

    return model, optimizer