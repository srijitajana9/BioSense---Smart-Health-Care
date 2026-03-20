# client_A.py (fixed)

import flwr as fl
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from utils import load_partition, encrypt_array, decrypt_array, encrypt_vector, decrypt_vector

# Load hospital A data
X, y = load_partition(0)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Create model
model = LogisticRegression(max_iter=1000)



# Helper to extract params safely and encrypt

def get_model_parameters(model):
    if hasattr(model, "coef_"):
        coef = encrypt_array(model.coef_)
        intercept = encrypt_vector(model.intercept_)
        # Convert to float arrays for Flower (simulate encryption for demo)
        coef = np.array(coef, dtype=np.float64)
        intercept = np.array(intercept, dtype=np.float64)
        return [coef, intercept]
    else:
        n_features = X_train.shape[1]
        coef = encrypt_array(np.zeros((1, n_features)))
        intercept = encrypt_vector(np.zeros(1))
        coef = np.array(coef, dtype=np.float64)
        intercept = np.array(intercept, dtype=np.float64)
        return [coef, intercept]

def set_model_parameters(model, parameters):
    coef, intercept = parameters
    coef = decrypt_array(coef)
    intercept = decrypt_vector(intercept)
    model.coef_, model.intercept_ = coef, intercept
    return model

class Client(fl.client.NumPyClient):
    def get_parameters(self, config): 
        return get_model_parameters(model)

    def fit(self, parameters, config):
        global model
        model = set_model_parameters(model, parameters)
        model.fit(X_train, y_train)
        return get_model_parameters(model), len(X_train), {}

    def evaluate(self, parameters, config):
        global model
        model = set_model_parameters(model, parameters)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        return float(acc), len(X_test), {"accuracy": acc}

fl.client.start_client(
    server_address="127.0.0.1:8080",
    client=Client().to_client(),
)
