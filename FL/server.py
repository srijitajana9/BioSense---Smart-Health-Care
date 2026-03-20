# server.py

import flwr as fl
import matplotlib.pyplot as plt
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_breast_cancer
from utils import decrypt_array, decrypt_vector

global_acc = []
final_parameters = None

# --- Encryption Setup (server holds private key) ---

def get_metrics(metrics):
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]
    avg_acc = sum(accuracies) / sum(examples)
    global_acc.append(avg_acc)
    print(f"Round Accuracy: {avg_acc:.4f}")
    return {"accuracy": avg_acc}

class SaveModelStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(self, rnd, results, failures):
        aggregated = super().aggregate_fit(rnd, results, failures)
        if aggregated is not None:
            global final_parameters
            final_parameters, _ = aggregated
        return aggregated

strategy = SaveModelStrategy(
    min_fit_clients=3,
    min_evaluate_clients=3,
    min_available_clients=3,
    evaluate_metrics_aggregation_fn=get_metrics,
)

hist = fl.server.start_server(
    server_address="127.0.0.1:8080",
    config=fl.server.ServerConfig(num_rounds=30),
    strategy=strategy,
)


# === Save final model ===
if final_parameters is not None:
    weights = fl.common.parameters_to_ndarrays(final_parameters)

    # Decrypt weights
    coef = decrypt_array(weights[0])
    intercept = decrypt_vector(weights[1])

    # Load dataset to create proper init
    X, y = load_breast_cancer(return_X_y=True)

    # Take subset which has at least 1 sample of each class
    idx_class0 = np.where(y == 0)[0][0]
    idx_class1 = np.where(y == 1)[0][0]
    X_dummy = np.vstack([X[idx_class0:idx_class0+1], X[idx_class1:idx_class1+1]])
    y_dummy = np.array([y[idx_class0], y[idx_class1]])

    model = LogisticRegression(max_iter=1000)
    model.fit(X_dummy, y_dummy)  # ✅ ensures 2 classes

    # Inject global weights
    model.coef_ = coef
    model.intercept_ = intercept

    joblib.dump(model, "global_model.pkl")
    print("✅ Global model saved as global_model.pkl")

# === Plot accuracy ===
rounds = list(range(1, len(global_acc) + 1))

# Create figure with better styling
plt.figure(figsize=(10, 6))
plt.plot(rounds, global_acc, marker="o", markersize=8, linewidth=2.5, 
         color='#2196F3', markerfacecolor='#1976D2', markeredgewidth=2, 
         markeredgecolor='white', label='Global Accuracy')

# Add grid for better readability
plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)

# Labels and title
plt.xlabel("Federated Rounds", fontsize=12, fontweight='bold')
plt.ylabel("Global Model Accuracy", fontsize=12, fontweight='bold')
plt.title("FL Training Progress", fontsize=14, fontweight='bold', pad=20)

# Add legend
plt.legend(loc='lower right', fontsize=10)

# Set y-axis to show more detail in the accuracy range
plt.ylim([min(global_acc) - 0.005, max(global_acc) + 0.005])

# Add value annotations for first, last, and min points
plt.annotate(f'{global_acc[0]:.4f}', xy=(1, global_acc[0]), 
             xytext=(1, global_acc[0] - 0.003), fontsize=9, ha='center')
plt.annotate(f'{global_acc[-1]:.4f}', xy=(len(global_acc), global_acc[-1]), 
             xytext=(len(global_acc), global_acc[-1] + 0.002), fontsize=9, ha='center')

# Tight layout for better spacing
plt.tight_layout()
plt.show()