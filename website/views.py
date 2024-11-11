from flask import Blueprint, render_template, request, send_from_directory, jsonify, redirect, url_for, current_app, Response
import pandas as pd
import joblib
import numpy as np
import csv
import os
import csv
import io
from .db_model import Data
from . import db
from flask_login import current_user

UPLOAD_FOLDER = 'uploads'

views = Blueprint('views', __name__)

model = joblib.load('random_forest_model.pkl')
scaler = joblib.load('scaler.pkl')

# Helper function to get the next user-specific prediction ID
def get_next_user_prediction_id(user_id):
    last_prediction = Data.query.filter_by(user_id=user_id).order_by(Data.user_prediction_id.desc()).first()
    if last_prediction:
        return last_prediction.user_prediction_id + 1
    else:
        return 1  # Start from 1 if no predictions exist

# Routes for the app
@views.route('/')
def home(): 
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Fetch previous data from the database for the current user only
    input_prediction_data = Data.query.filter_by(user_id=current_user.id).all()

    # Prepare data for the first accordion (Inputs and Predicted Grades)
    csv_data = [
        {
            'studentid': row.user_prediction_id,
            'attendance': round(row.attendance),
            'previous_grades': row.previousGrade,
            'financial_situation': row.financialSituation,
            'learning_environment': row.learningEnvironment,
            'predicted_grade': round(row.predictedGrade, 2),
            'remarks': row.remarks
        }
        for row in input_prediction_data
    ]

    # Prepare data for the second accordion (Student No. and Predicted Grade)
    stored_predictions = [
        {
            'student_id': row.user_prediction_id, 
            'predicted_grade': round(row.predictedGrade, 2), 
            'remarks': row.remarks}
        for row in input_prediction_data
    ]

    return render_template("home.html", csv_data=csv_data, stored_predictions=stored_predictions)

# Helper function to get the next user-specific prediction ID
def get_next_user_prediction_id(user_id):
    last_prediction = Data.query.filter_by(user_id=user_id).order_by(Data.user_prediction_id.desc()).first()
    if last_prediction:
        return last_prediction.user_prediction_id + 1
    else:
        return 1  # Start from 1 if no predictions exist

# Helper function to classify grades
def classify_grade(grade):
    if grade >= 90:
        return "Outstanding"
    elif 85 <= grade < 90:
        return "Very Satisfactory"
    elif 80 <= grade < 85:
        return "Satisfactory"
    elif 75 <= grade < 80:
        return "Fairly Satisfactory"
    else:
        return "Did not Meet Expectations"

# Route to predict based on manual input
@views.route('/predict', methods=['POST'])
def predict():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not authenticated'}), 401

    data = request.json
    try:
        attendance = float(data['attendance'])
        previous_grades = float(data['previous_grades'])
        financial_situation = float(data['financial_situation'])
        learning_environment = float(data['learning_environment'])



        print("Received data:", data)

        # Parse the incoming JSON data
        days_present = float(data['days_present'])
        school_days = float(data['school_days'])

        # Validate: Days Present should not be negative
        if days_present < 0:
            return jsonify({'error': 'Days present cannot be negative.'}), 400

        # Validate: School days must be greater than or equal to days present
        if days_present > school_days:
            return jsonify({'error': 'Days present cannot exceed total school days.'}), 400

        # Calculate attendance percentage
        attendance = (days_present / school_days) * 100

        previous_grades = float(data['previous_grades'])
        financial_situation = float(data['financial_situation'])
        learning_environment = float(data['learning_environment'])
        
    except (KeyError, ValueError) as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400

    # Prepare features for prediction
    features = np.array([attendance, financial_situation, learning_environment, previous_grades]).reshape(1, -1)
    features = scaler.transform(features)
    
    # Predict the grade
    prediction = model.predict(features)[0]
    prediction = round(prediction, 2)

    # Classify the predicted grade
    remarks = classify_grade(prediction)

    # Get the next user-specific prediction ID
    user_prediction_id = get_next_user_prediction_id(current_user.id)

    # Create a new data entry in the database
    new_data = Data(
        attendance=attendance,
        previousGrade=previous_grades,
        financialSituation=financial_situation,
        learningEnvironment=learning_environment,
        predictedGrade=prediction,
        remarks=remarks,  # Store remarks
        user_id=current_user.id,
        user_prediction_id=user_prediction_id  # Store the user-specific ID
    )
    
    db.session.add(new_data)
    db.session.commit()

    # Return the prediction, user-specific ID, and remarks as a JSON response
    return jsonify({
        'prediction': round(prediction, 2),
        'student_id': new_data.user_prediction_id,
        'remarks': remarks  # Return remarks to the frontend
    })

import re  # For pattern matching

@views.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return '<script>alert("No file part in the request."); window.location.href="/";</script>'

    file = request.files['file']
    if file.filename == '':
        return '<script>alert("No selected file."); window.location.href="/";</script>'

    if file and file.filename.endswith('.csv'):
        # Ensure the upload directory exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)

        try:
            # Save the uploaded file
            file.save(filepath)
        except PermissionError as e:
            return f'<script>alert("Permission error: {e}"); window.location.href="/";</script>'

        # Process the CSV file
        df = pd.read_csv(filepath)

        # Check if the required columns exist (notice no 'attendance' in required columns anymore)
        required_columns = ['days_present', 'school_days', 'financial_situation', 'learning_environment', 'previous_grades']
        if not all(col in df.columns for col in required_columns):
            return '<script>alert("Missing required columns in the uploaded CSV file."); window.location.href="/";</script>'

        # Validate and calculate attendance dynamically
        for index, row in df.iterrows():
            try:
                # Days Present and School Days should be numeric values
                days_present = float(row['days_present'])
                school_days = float(row['school_days'])

                # Validate the days present and school days
                if days_present < 0:
                    return f'<script>alert("Invalid data in row {index+1}: Days present cannot be negative."); window.location.href="/";</script>'
                if days_present > school_days:
                    return f'<script>alert("Invalid data in row {index+1}: Days present cannot exceed total school days."); window.location.href="/";</script>'

                # Calculate attendance percentage
                attendance = (days_present / school_days) * 100  # Calculate and use attendance dynamically

                # Ensure other columns are numeric
                financial_situation = float(row['financial_situation'])
                learning_environment = float(row['learning_environment'])
                previous_grade = float(row['previous_grades'])
                
            except ValueError:
                return f'<script>alert("Invalid data in row {index+1}: Numeric values are expected for days_present, school_days, financial_situation, learning_environment, and previous grades."); window.location.href="/";</script>'

            try:
                # Prepare features for prediction
                features = np.array([attendance, financial_situation, learning_environment, previous_grade]).reshape(1, -1)
                features_scaled = scaler.transform(features)
                prediction = model.predict(features_scaled)[0]

                # Classify the predicted grade
                remarks = classify_grade(prediction)

                # Get the next user-specific prediction ID
                user_prediction_id = get_next_user_prediction_id(current_user.id)

                # Save data and prediction to the database
                new_data = Data(
                    attendance=attendance,  # Use the calculated attendance
                    previousGrade=previous_grade,
                    financialSituation=financial_situation,
                    learningEnvironment=learning_environment,
                    predictedGrade=prediction,
                    remarks=remarks,  # Store remarks
                    user_id=current_user.id,
                    user_prediction_id=user_prediction_id  # Assign user-specific prediction ID here
                )
                db.session.add(new_data)

            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue

        db.session.commit()  # Commit all new entries to the database
        return '<script>alert("File uploaded and processed successfully."); window.location.href="/";</script>'

    return '<script>alert("Invalid file format. Please upload a CSV file."); window.location.href="/";</script>'


import csv
import io
from flask import Response

@views.route('/download-template', methods=['GET'])
def download_template():
    # Create a string buffer to hold the CSV data
    output = io.StringIO()
    
    # Create a CSV writer object
    writer = csv.writer(output)
    
    # Write the header for the template
    writer.writerow(['days_present', 'school_days', 'previous_grades', 'financial_situation', 'learning_environment'])
    
    # Seek to the beginning of the StringIO object
    output.seek(0)
    
    # Create a response object with the CSV data
    response = Response(output, mimetype='text/csv')
    
    # Set the headers to indicate this is a file download
    response.headers['Content-Disposition'] = 'attachment; filename=template.csv'
    
    return response


