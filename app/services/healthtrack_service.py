import pickle

# Load the trained model
with open('app/models/decision_tree_model.pkl', 'rb') as file:
    model = pickle.load(file)

def predict_health_risk(features):
    try:
        prediction = model.predict(features)
        if prediction[0] == 1:
            return "Low Risk"
        elif prediction[0] == 0:
            return "High Risk"
        else:
            return "Medium Risk"
    except Exception as e:
        raise RuntimeError(f"Error in prediction: {str(e)}")
