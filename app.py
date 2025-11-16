from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# ============================================================================
# LOAD YOUR TRAINED MODEL
# ============================================================================

# Load model (change path to where you saved your best model)
try:
    with open('models/best_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print("✓ Model loaded successfully!")
except Exception as e:
    print(f"⚠ Error loading model: {e}")
    model = None

# Load scaler if you saved it during preprocessing
try:
    with open('models/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("✓ Scaler loaded successfully!")
except:
    scaler = None
    print("⚠ Scaler not found - will create new one")

# Feature names (from your preprocessing)
FEATURE_NAMES = [
    'VISITMO', 'VISITDAY', 'VISITYR', 'NACCVNUM', 'BIRTHMO', 'BIRTHYR', 
    'SEX', 'HISPANIC', 'HISPOR', 'RACE', 'RACESEC', 'RACETER', 
    'PRIMLANG', 'EDUC', 'MARISTAT', 'NACCLIVS', 'INDEPEND', 'RESIDENC', 
    'HANDED', 'NACCAGE', 'NACCAGEB', 'INBIRMO', 'INBIRYR', 'INSEX', 
    'INHISP', 'INRACE', 'INEDUC', 'INRELTO', 'INLIVWTH', 'INVISITS', 
    'INCALLS', 'INRELY', 'NACCFAM', 'NACCMOM', 'NACCDAD', 'TOBAC30', 
    'TOBAC100', 'SMOKYRS', 'PACKSPER', 'QUITSMOK', 'ALCOCCAS', 'ALCFREQ', 
    'HEIGHT', 'WEIGHT', 'BPSYS', 'BPDIAS', 'HRATE', 'BILLS', 'TAXES', 
    'SHOPPING', 'GAMES', 'STOVE', 'MEALPREP', 'EVENTS', 'PAYATTN', 
    'REMDATES', 'TRAVEL'
]

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/questionnaire')
def questionnaire():
    """Questionnaire page"""
    return render_template('questionnaire.html')

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    Receives form data, processes it, returns risk prediction
    """
    try:
        # Get form data
        form_data = request.get_json()
        
        # Convert form responses to model features
        features = process_form_data(form_data)
        
        # Make prediction
        if model is not None:
            # Get probability
            probability = model.predict_proba([features])[0][1]
            risk_percentage = float(probability * 100)
            
            # Get binary prediction
            prediction = int(model.predict([features])[0])
            
            # Determine risk category
            if risk_percentage < 30:
                risk_category = "Low Risk"
                risk_color = "#00d97e"
            elif risk_percentage < 70:
                risk_category = "Medium Risk"
                risk_color = "#ffc107"
            else:
                risk_category = "At Risk"
                risk_color = "#dc3545"
            
            # Generate personalized recommendations
            recommendations = generate_recommendations(features, form_data)
            
            return jsonify({
                'success': True,
                'risk_percentage': round(risk_percentage, 1),
                'risk_category': risk_category,
                'risk_color': risk_color,
                'prediction': prediction,
                'recommendations': recommendations
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Model not loaded'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results')
def results():
    """Results page"""
    return render_template('results.html')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def process_form_data(form_data):
    """
    Convert questionnaire responses to model features
    This is the KEY function - maps your form to model input
    """
    
    # Initialize feature vector with defaults
    features = {}
    
    # Section 1: Demographics
    features['born_before_1970'] = 1 if form_data.get('born_before_1970') == 'yes' else 0
    features['sex_male'] = 1 if form_data.get('sex_male') == 'yes' else 0
    features['hispanic_latino'] = 1 if form_data.get('hispanic_latino') == 'yes' else 0
    features['racial_minority'] = 1 if form_data.get('racial_minority') == 'yes' else 0
    features['education_years'] = 1 if form_data.get('education_years') == 'yes' else 0
    features['married_partnered'] = 1 if form_data.get('married_partnered') == 'yes' else 0
    features['right_handed'] = 1 if form_data.get('right_handed') == 'yes' else 0
    
    # Section 2: Background
    features['english_country'] = 1 if form_data.get('english_country') == 'yes' else 0
    features['spanish_environment'] = 1 if form_data.get('spanish_environment') == 'yes' else 0
    features['speak_english'] = 1 if form_data.get('speak_english') == 'yes' else 0
    features['speak_spanish'] = 1 if form_data.get('speak_spanish') == 'yes' else 0
    
    # Section 3: Vision & Hearing
    features['vision_without_glasses'] = 1 if form_data.get('vision_without_glasses') == 'yes' else 0
    features['vision_with_glasses'] = map_vision_hearing(form_data.get('vision_with_glasses'))
    features['hearing_without_aid'] = 1 if form_data.get('hearing_without_aid') == 'yes' else 0
    features['hearing_with_aid'] = map_vision_hearing(form_data.get('hearing_with_aid'))
    
    # Section 4: Health
    features['height_above_150'] = 1 if form_data.get('height_above_150') == 'yes' else 0
    features['weight_above_50'] = 1 if form_data.get('weight_above_50') == 'yes' else 0
    features['heart_rate_normal'] = map_unsure(form_data.get('heart_rate_normal'))
    features['systolic_bp'] = map_unsure(form_data.get('systolic_bp'))
    features['diastolic_bp'] = map_unsure(form_data.get('diastolic_bp'))
    
    # Section 5: Smoking
    features['smoking_history'] = 1 if form_data.get('smoking_history') == 'yes' else 0
    
    # Section 6: Platform
    features['first_time_user'] = 1 if form_data.get('first_time_user') == 'yes' else 0
    features['answering_in_english'] = 1 if form_data.get('answering_in_english') == 'yes' else 0
    features['remote_response'] = 1 if form_data.get('remote_response') == 'yes' else 0
    
    # Convert to array in correct order (this MUST match your model's training features)
    # You'll need to adjust this based on your actual feature names
    feature_array = [features.get(key, 0) for key in sorted(features.keys())]
    
    return feature_array

def map_vision_hearing(value):
    """Map vision/hearing responses to numeric"""
    if value == 'yes':
        return 1
    elif value == 'no':
        return 0
    else:  # 'na'
        return 0.5

def map_unsure(value):
    """Map unsure responses to numeric"""
    if value == 'yes':
        return 1
    elif value == 'no':
        return 0
    else:  # 'unsure'
        return 0.5

def generate_recommendations(features, form_data):
    """Generate personalized recommendations based on responses"""
    recommendations = []
    
    # Education-based recommendation
    if form_data.get('education_years') == 'no':
        recommendations.append({
            'icon': '📚',
            'title': 'Cognitive Engagement',
            'text': 'Engage in mentally stimulating activities like reading, puzzles, or learning new skills to build cognitive reserve.'
        })
    
    # Social connection
    if form_data.get('married_partnered') == 'no':
        recommendations.append({
            'icon': '👥',
            'title': 'Social Connection',
            'text': 'Maintain strong social ties. Join clubs, volunteer, or regularly connect with friends and family.'
        })
    
    # Smoking
    if form_data.get('smoking_history') == 'yes':
        recommendations.append({
            'icon': '🚭',
            'title': 'Quit Smoking',
            'text': 'If you currently smoke, consider quitting. Smoking cessation can reduce dementia risk at any age.'
        })
    
    # Hearing
    if form_data.get('hearing_without_aid') == 'no':
        recommendations.append({
            'icon': '👂',
            'title': 'Hearing Health',
            'text': 'Untreated hearing loss is linked to cognitive decline. Consider getting a hearing evaluation.'
        })
    
    # Always include these general recommendations
    recommendations.extend([
        {
            'icon': '🥗',
            'title': 'Brain-Healthy Diet',
            'text': 'Follow the MIND diet rich in vegetables, berries, whole grains, fish, and healthy fats.'
        },
        {
            'icon': '🏃',
            'title': 'Physical Activity',
            'text': 'Aim for 150 minutes of moderate exercise weekly. Physical activity benefits brain health.'
        },
        {
            'icon': '😴',
            'title': 'Quality Sleep',
            'text': 'Prioritize 7-8 hours of quality sleep. Good sleep helps clear brain waste products.'
        },
        {
            'icon': '🧘',
            'title': 'Stress Management',
            'text': 'Practice stress-reduction techniques like meditation, yoga, or deep breathing exercises.'
        }
    ])
    
    return recommendations[:6]  # Return top 6 recommendations

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)