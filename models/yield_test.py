import pandas as pd
import numpy as np
import joblib

data = pd.read_csv('Datasets/mini_crop_yield.csv')

# Prediction function
def predict_yield(Season, State, Crop, Annual_Rainfall, user_land_area):
    # Load the model and encoders
    best_rf = joblib.load('Trained_models/best_rf_model.pkl')
    label_encoder_crop = joblib.load('Trained_models/label_encoder_crop.pkl')
    label_encoder_season = joblib.load('Trained_models/label_encoder_season.pkl')
    label_encoder_state = joblib.load('Trained_models/label_encoder_state.pkl')

    state_encoded = label_encoder_state.transform([State])[0]
    crop_encoded = label_encoder_crop.transform([Crop])[0]
    season_encoded = label_encoder_season.transform([Season])[0]
    
    # You can set the season and fertilizer/pesticide use accordingly or take user input
    # Here, I'm assuming some average values or set values
    fertilizer_avg = data['Fertilizer (kg)'].mean()
    pesticide_avg = data['Pesticide (kg)'].mean()

    input_data = np.array([[crop_encoded, season_encoded, state_encoded, Annual_Rainfall, fertilizer_avg, pesticide_avg]])
    predicted_yield = best_rf.predict(input_data)[0]
    
    # Finding the closest area from the dataset
    closest_index = (data['Yield (metric tons/hectares)'] - predicted_yield).abs().idxmin()
    matching_row = data.iloc[closest_index]
    area = matching_row['Area (Hectares)']

    # Calculating final production
    final_production = predicted_yield * (user_land_area / 3.954)
    
    return final_production, predicted_yield
