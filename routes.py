from flask import Flask, render_template, request, url_for, jsonify, make_response, flash, redirect
from markupsafe import Markup
from flask_login import login_required, login_user, logout_user, current_user
from functools import wraps
import pickle
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import joblib
from app import app, db, User
import subprocess
import os
import sys


# ---------------------------------------------------------------------------
# Deserializing ML models
# ---------------------------------------------------------------------------
kmeanclus  = pickle.load(open('./Prediction/kmean.pkl', 'rb'))
kprotoclus = joblib.load('./Prediction/kproto.pkl')
rdcls      = joblib.load('./Prediction/cls.pkl')
lr         = joblib.load('./Prediction/models.pkl')


# ---------------------------------------------------------------------------
# Exponential Smoothing
# ---------------------------------------------------------------------------
class ExponentialSmoothing:
    def __init__(self, alpha):
        self.alpha = alpha

    def fit(self, data):
        self.data = data

    def predict(self, year):
        # Apply exponential smoothing to the data
        smoothed_data = [self.data[0]]
        for i in range(1, len(self.data)):
            smoothed_data.append(
                self.alpha * self.data[i] + (1 - self.alpha) * smoothed_data[i - 1]
            )

        # Predict the value for the specified year using the smoothed data
        if year < len(self.data):
            return smoothed_data[year]
        else:
            last_value = smoothed_data[-1]
            for i in range(len(self.data), year):
                last_value = self.alpha * self.data[-1] + (1 - self.alpha) * last_value
            return last_value


# ---------------------------------------------------------------------------
# Population Projection Formula — Geometric Growth Method
# ---------------------------------------------------------------------------
import math

def projection(v1, v2, yr1, yr2, year):
    t = yr2 - yr1
    n = year - yr2
    r = math.pow(v2 / v1, 1 / t) - 1
    P = v2 * math.pow(1 + r, n)
    return P


# ===========================================================================
# RBAC — Role-Required Decorator
# ===========================================================================

def role_required(*allowed_roles):
    """
    Factory decorator that restricts a view to users whose role is in
    `allowed_roles`. Redirects unauthenticated or unauthorised users to
    the login page with a flash message.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash('Unauthorized access level.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ===========================================================================
# Template Context Processor — injects current_user into every template
# ===========================================================================

@app.context_processor
def inject_current_user():
    """Make current_user available to every Jinja2 template automatically."""
    return dict(current_user=current_user)


# ===========================================================================
# Authentication Routes
# ===========================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Already logged-in users skip the login page
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    response = make_response(redirect(url_for('login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma']        = 'no-cache'
    response.headers['Expires']       = '0'
    return response


# ===========================================================================
# Public & Field Officer Allowed Routes (public | field_officer)
# ===========================================================================

@app.route('/')
@app.route('/index')
@login_required
@role_required('public', 'field_officer')
def index():
    return render_template('index.html')


@app.route('/about')
@app.route('/About')
@login_required
@role_required('public', 'field_officer')
def about():
    return render_template('About.html')


@app.route('/feedback')
@app.route('/Feedback')
@login_required
@role_required('public', 'field_officer')
def feedback():
    return render_template('Feedback.html')


# Google Charts analysis
@app.route('/analysis')
@login_required
@role_required('public', 'field_officer')
def analysis():
    return render_template('Analysis.html')


# Plotly Charts analysis
@app.route('/analysis2')
@login_required
@role_required('public', 'field_officer')
def analysis2():
    return render_template('Analysis2.html')


# Geospatial analysis
@app.route('/analysis3')
@login_required
@role_required('public', 'field_officer')
def analysis3():
    return render_template('Analysis3(maps).html')


# Serving plot HTML files & resources (required for analysis2 & analysis3 iframes)
@app.route('/plots/<path:filename>')
@login_required
@role_required('public', 'field_officer')
def serve_plots(filename):
    return render_template(f'plots/{filename}')


# ===========================================================================
# Field Officer Allowed Routes (field_officer) — Complete Operational Access
# ===========================================================================

@app.route('/Kmeans')
@app.route('/kmeans')
@app.route('/kmean')
@login_required
@role_required('field_officer')
def Kmeans():
    return render_template("K-Means.html")


@app.route('/KMeansanalysis', methods=['POST'])
@login_required
@role_required('field_officer')
def KMeansanalysis():
    features = [x for x in request.form.values()]
    state_target = features[0].upper()
    district_target = features[1]

    # Reading labelled and scaled data
    df = pd.read_csv("Datasets/kmeansflask2.csv")
    df_filtered = df.loc[(df["STATE/UT"] == state_target) & (df["DISTRICT"] == district_target)]
    years = df_filtered['YEAR'].values

    if len(years) == 0:
        return render_template('K-Means.html', prediction_text0="No historical data found for this district")

    clusters = []
    for i in years:
        l = df_filtered.loc[df_filtered["YEAR"] == i].values
        final_features = [[x for x in l[0] if type(x) == float]]
        y_pred = kmeanclus.predict(final_features)
        clusters.append(y_pred[0])  # 0-high, 1-low, 2-moderate

    # Finding Mode
    high     = clusters.count(0)
    low      = clusters.count(1)
    moderate = clusters.count(2)

    if high > low and high > moderate:
        label = "RED ZONE"
    elif low > high and low > moderate:
        label = "GREEN ZONE"
    elif moderate > high and moderate > low:
        label = "ORANGE ZONE"
    else:
        if high == moderate == low:
            label = "Crime Rate Varies a Lot"
        elif high == moderate:
            label = "Red-Orange Zone(Lies between Orange Zone and Red Zone)"
        elif low == moderate:
            label = "Yellow Zone(Lies between Green Zone and Orange Zone)"
        else:
            label = "Crime Rate Varies a Lot"

    return render_template('K-Means.html', prediction_text0=label)


@app.route('/Randomfrstcls')
@app.route('/randomfrstcls', methods=['GET'])
@app.route('/randomforest')
@login_required
@role_required('field_officer')
def Randomfrstcls():
    return render_template("RandomForestClassifer.html")


@app.route('/randomfrstcls', methods=['POST'])
@login_required
@role_required('field_officer')
def randomfrstcls():
    try:
        form_vals     = list(request.form.values())
        state_name    = form_vals[0].upper()
        district_name = form_vals[1]
        year          = int(form_vals[2])

        # Encode state and district
        enc_df = pd.read_csv("Datasets/encoded.csv")
        arr    = (enc_df.loc[enc_df["STATE/UT"] == state_name]
                        .loc[enc_df["DISTRICT"] == district_name].values)
        if len(arr) == 0:
            return render_template("RandomForestClassifer.html",
                                   prediction_text="ERROR: District not found in database.")
        state_enc    = int(arr[0][3])
        district_enc = int(arr[0][4])

        # Load classification dataset
        df1 = pd.read_csv("Datasets/classfication_data_with_cluster_labels.csv")
        df1.drop(["Unnamed: 0"], axis=1, inplace=True)

        crime_cols    = list(df1.columns[3:11])  # 8 crime columns
        district_data = df1.loc[
            (df1["STATE/UT"] == state_enc) & (df1["DISTRICT"] == district_enc)
        ]

        if len(district_data) == 0:
            return render_template("RandomForestClassifer.html",
                                   prediction_text="ERROR: No historical data found for this district.")

        t   = year - district_data['YEAR'].values[-1]
        obj = ExponentialSmoothing(0.3)

        predicted_crimes = []
        for col in crime_cols:
            l = district_data[col].values
            obj.fit(l)
            predicted_crimes.append(int(obj.predict(t)))

        # Build named DataFrame matching model's 11 feature columns
        feature_names  = ['STATE/UT', 'DISTRICT', 'YEAR', 'MURDER', 'ATTEMPT TO MURDER',
                          'RAPE', 'KIDNAPPING & ABDUCTION', 'DACOITY', 'ROBBERY', 'THEFT',
                          'HURT/GREVIOUS HURT']
        feature_values = [state_enc, district_enc, year] + predicted_crimes

        # FIX BUG: Use columns=feature_names (previously was feature_values!)
        input_df       = pd.DataFrame([feature_values], columns=feature_names)

        # Use the Random Forest classifier (rdcls loaded from cls.pkl)
        y_pred = rdcls.predict(input_df)

        if y_pred[0] == 1:
            label = "RED ZONE"
        elif y_pred[0] == 2:
            label = "GREEN ZONE"
        elif y_pred[0] == 3:
            label = "ORANGE ZONE"
        else:
            label = "UNKNOWN ZONE"

        # Replace encoded values with readable names for display
        display_df              = input_df.copy()
        display_df['STATE/UT']  = form_vals[0]
        display_df['DISTRICT']  = district_name

        return render_template("RandomForestClassifer.html",
                               prediction_text=label + ' ' + str(list(display_df.values)))

    except Exception as e:
        return render_template("RandomForestClassifer.html",
                               prediction_text=f"ERROR: {str(e)}")


# Linear Regression
@app.route('/LinearReg')
@app.route('/linearreg', methods=['GET'])
@app.route('/linearregression')
@login_required
@role_required('field_officer')
def LinearReg():
    return render_template("linear-regression.html")


@app.route('/linearreg', methods=["POST"])
@login_required
@role_required('field_officer')
def linearreg():
    try:
        features   = list(request.form.values())
        state      = features[0]
        year       = int(features[1])

        df         = pd.read_csv("Datasets/data.csv")
        state_data = df.loc[df["State/UT"] == state]

        if len(state_data) == 0:
            return render_template("linear-regression.html",
                                   prediction_text=f"ERROR: State '{state}' not found in dataset.")

        if state not in lr:
            return render_template("linear-regression.html",
                                   prediction_text=f"ERROR: No regression model available for '{state}'.")

        a1 = state_data['Population (in lakhs)'].values[0]
        a2 = state_data['Population (in lakhs)'].values[-1]
        y1 = int(state_data['Year'].values[0])
        y2 = int(state_data['Year'].values[-1])

        estimated_population = projection(a1, a2, y1, y2, year)
        y_pred               = lr[state].predict(pd.DataFrame([[int(estimated_population)]]))
        predicted_crimes     = int(y_pred[0])
        crime_rate           = int(predicted_crimes / estimated_population)

        result = (f'Total IPC Crimes: {predicted_crimes:,}'
                  f', Projected Population: {int(estimated_population):,} Lakhs'
                  f', Crime Rate: {crime_rate} (per lakh)')
        return render_template("linear-regression.html", prediction_text=result)

    except Exception as e:
        return render_template("linear-regression.html",
                               prediction_text=f"ERROR: {str(e)}")


# Time Series Forecasting
@app.route('/timeseriesipc')
@login_required
@role_required('field_officer')
def timeseriesipc():
    return render_template('total-ipc-forecasting.html')


@app.route('/timeseriescr')
@login_required
@role_required('field_officer')
def timeseriescr():
    return render_template('time-series-forcasting.html')


# Data Display
@app.route('/datadisp')
@login_required
@role_required('field_officer')
def datadisp():
    return render_template('datadisplay.html')


# Run File
@app.route("/run-file")
@login_required
@role_required('field_officer')
def run_file():
    file_path = os.path.join("folium-map", "index.py")
    subprocess.Popen([sys.executable, file_path])
    return {"message": "File execution initiated"}


# Crime Feed
@app.route('/crimefeed')
@login_required
@role_required('field_officer')
def crimefeed():
    response = make_response(render_template('crimefeed.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma']        = 'no-cache'
    response.headers['Expires']       = '0'
    return response


# Heat Map
@app.route('/foliummap')
@login_required
@role_required('field_officer')
def foliummap():
    return render_template("final.html")
