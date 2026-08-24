import os
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Load Dataset
dataset_path = os.path.join("Datasets", "01_District_wise_crimes_committed_IPC_2001_2012.csv")
df = pd.read_csv(dataset_path)

if "Unnamed: 0" in df.columns:
    df.drop(["Unnamed: 0"], axis=1, inplace=True)

# Extract 10 crime columns
crime_cols = [c for c in df.columns if c not in ['STATE/UT', 'DISTRICT', 'YEAR']]

# Create dummy cluster labels (0, 1, 2)
df['total'] = df[crime_cols].sum(axis=1)
df['cluster'] = pd.qcut(df['total'], q=3, labels=[0, 1, 2])

# 2. Features expected by routes.py (11 total: 10 crime columns + YEAR)
features = crime_cols + ['YEAR']
X = df[features]
y = df['cluster'].astype(int)

# 3. Train models
dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X, y)

rf_model = RandomForestClassifier(random_state=42)
rf_model.fit(X, y)

# 4. Overwrite ALL possible model names in Prediction directory
os.makedirs('./Prediction', exist_ok=True)

pickle_names = ['cls.pkl', 'rdcls.pkl', 'rf.pkl', 'random_forest.pkl', 'model.pkl']

for name in pickle_names:
    filepath = os.path.join('./Prediction', name)
    joblib.dump(dt_model if 'cls' in name else rf_model, filepath)
    print(f"Saved: {filepath}")

print("\nAll model files rebuilt successfully with 11 features!")