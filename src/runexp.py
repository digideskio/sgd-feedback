import json
import pickle
import os
from argparse import ArgumentParser

import numpy as np
from keras.datasets import mnist
from keras.utils import np_utils

from gridopts import *
from models import *
from dna import DNAMonitor

LRS = np.logspace(-6, -1, 10)
DATASET_LOADERS = {
    "mnist": mnist.load_data
}

arg_parser = ArgumentParser()
arg_parser.add_argument("--optimizer", type=str, required=True, choices=OPTIMIZERS_INDEX.keys())
arg_parser.add_argument("--opt-args", type=json.loads, default={})
arg_parser.add_argument("--model", type=str, required=True, choices=MODEL_FACTORIES.keys())
arg_parser.add_argument("--dataset", type=str, required=True, choices=DATASET_LOADERS.keys())
arg_parser.add_argument("--batch-size", type=int, required=True)
arg_parser.add_argument("--epochs", type=int, required=True)
args = arg_parser.parse_args()

args.opt_args["lrs"] = LRS
grid_opt = OPTIMIZERS_INDEX[args.optimizer](**args.opt_args)

(X_train, y_train), _ = DATASET_LOADERS[args.dataset]()
X_train = X_train.reshape((X_train.shape[0], -1)).astype("float32") / 255.
y_train = np_utils.to_categorical(y_train, 10)

best_final_loss = np.inf
for opt in grid_opt:
    model = MODEL_FACTORIES[args.model]()
    model.compile(optimizer=opt, loss="categorical_crossentropy")
    if args.optimizer == "dna":
        dna_monitor = DNAMonitor()
        callbacks = [dna_monitor]
    else:
        callbacks = []
    history = model.fit(x=X_train, y=y_train, batch_size=args.batch_size, nb_epoch=args.epochs, verbose=1, callbacks=callbacks)

    if history.history["loss"][-1] < best_final_loss:
        best_final_loss = history.history["loss"][-1]
        best_loss_history = history.history["loss"]
        best_opt_config = opt.get_config()
        if args.optimizer == "dna":
            best_dna_monitor = dna_monitor

save_data = {
    "best_loss_history": best_loss_history,
    "param_grid": grid_opt.grid,
    "best_opt_config": best_opt_config,
    "batch_size": args.batch_size,
    "epochs": args.epochs
}
if args.optimizer == "dna":
    save_data["best_batch_loss_history"] = best_dna_monitor.batch_losses
    save_data["ds"] = best_dna_monitor.ds
with open(os.path.join("data", "{}".format(args.model), "{}".format(args.dataset), "{}.pkl".format(args.optimizer)), "wb") as f:
    pickle.dump(save_data, f)
