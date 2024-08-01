import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
import joblib

# Load dataset
data = pd.read_csv('Datasets/mini_crop_yield.csv')

# Data preprocessing
data['Season'] = data['Season'].str.strip()  # Remove any leading/trailing spaces
label_encoder_crop = LabelEncoder()
label_encoder_season = LabelEncoder()
label_encoder_state = LabelEncoder()
data['Crop'] = label_encoder_crop.fit_transform(data['Crop'])
data['Season'] = label_encoder_season.fit_transform(data['Season'])
data['State'] = label_encoder_state.fit_transform(data['State'])

# Feature selection
X = data[['Crop', 'Season', 'State', 'Annual_Rainfall (mm)', 'Fertilizer (kg)', 'Pesticide (kg)']]
y = data['Yield (metric tons/hectares)']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training with hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

rf = RandomForestRegressor(random_state=42)
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2)
grid_search.fit(X_train, y_train)

# Best model
best_rf = grid_search.best_estimator_

# Save the model and encoders
joblib.dump(best_rf, 'Trained_models/best_rf_model.pkl')
joblib.dump(label_encoder_crop, 'Trained_models/label_encoder_crop.pkl')
joblib.dump(label_encoder_season, 'Trained_models/label_encoder_season.pkl')
joblib.dump(label_encoder_state, 'Trained_models/label_encoder_state.pkl')
