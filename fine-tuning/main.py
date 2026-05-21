import argparse
from data_utils import load_process_data
from torch.utils.data import DataLoader
from load_model import load_model
import mlflow
from training import train, evaluate
import numpy as np

def main(args):

    with mlflow.start_run():
    # Log parameters
        mlflow.log_params({
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "epochs": args.nepochs,
            "weight_decay": 0.01
        })

        test_accs = []

        model, optimizer = load_model(args)

        train_data = load_process_data("train")
        test_data = load_process_data("test")

        batch_size = int(args.batch_size)
        train_dataloader = DataLoader(train_data, batch_size=batch_size // 2, shuffle=True)
        test_dataloader = DataLoader(test_data, batch_size=batch_size // 2, shuffle=False)

        nepochs = int(args.nepochs)
        for epoch in range(1, nepochs + 1):
            print('Epoch', epoch)
            train(model, optimizer, train_dataloader, epoch)
            print("train acc")
            train_acc = evaluate(model, train_dataloader)
            print("test acc")
            test_acc = evaluate(model, test_dataloader)

            mlflow.log_metric("train_acc", train_acc, step=epoch)
            mlflow.log_metric("test_acc", test_acc, step=epoch)

        test_accs.append(test_acc)

    mlflow.log_metric("best_accuracy", np.max(test_accs))
    mlflow.pytorch.log_model(model, "model")
    return np.max(test_accs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nepochs")
    parser.add_argument("--batch_size")
    parser.add_argument("--learning_rate")
    args = parser.parse_args()

    main(args)