import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Load data
df = pd.read_csv('2023_revised.csv')
df = pd.get_dummies(df)

# Separate features and target (grades)
X = df.drop(['grades'], axis=1)
y = df['grades']

# Normalize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data into 80% training, 10% validation, 10% test sets
X_train, X_temp, y_train, y_temp = train_test_split(X_scaled, y, test_size=0.2, random_state=19)  # 80% train, 20% temp
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=19)  # 10% val, 10% test

param_grid = {
    'n_estimators': [10, 50],
    'max_depth': [None, 5, 10],
    'min_samples_split': [2, 4],
    'min_samples_leaf': [1, 2],
    'max_features': ['sqrt', 'log2'], 
    'bootstrap': [True],
}


# Define the model
rfr = RandomForestRegressor(random_state=13, bootstrap=True)

# Setup GridSearchCV
grid_search = GridSearchCV(estimator=rfr, param_grid=param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)

# Fit GridSearchCV
grid_search.fit(X_train, y_train)

best_rfr = grid_search.best_estimator_

# Save the model and scaler
joblib.dump(best_rfr, 'random_forest_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
