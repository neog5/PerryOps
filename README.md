# PerryOps - Preoperative Optimization System

A backend API for automating preoperative optimization recommendations and medication reminders using Firebase.

## Features

- **AI-Powered Recommendations**: Generate medication schedules using AI models
- **CPC Staff Approval**: Human validation of AI recommendations
- **Push Notifications**: Firebase Cloud Messaging for medication reminders
- **Compliance Tracking**: Monitor patient adherence to recommendations
- **Optimization Status**: Determine if patients are ready for surgery

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Firebase**: Backend-as-a-Service with Firestore, Auth, and Cloud Messaging
- **Python**: Simple and clean API implementation

## Quick Start

### 1. Setup Firebase

1. Go to [Firebase Console](https://console.firebase.google.com) and create a new project
2. Enable Firestore Database and Cloud Messaging
3. Create a service account and download the JSON key
4. Get your project ID from Project Settings

### 2. Configure Environment

Create a `.env` file:
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
DEBUG=True
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

### 5. Access API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Patients
- `POST /patients/` - Create a new patient
- `GET /patients/` - Get all patients
- `GET /patients/{patient_id}` - Get specific patient
- `GET /patients/{patient_id}/schedule` - Get patient's medication schedule

### Recommendations
- `POST /recommendations/generate` - Generate AI recommendations
- `GET /recommendations/pending` - Get pending recommendations for CPC staff
- `POST /recommendations/{id}/approve` - Approve recommendation
- `POST /recommendations/{id}/reject` - Reject recommendation

### Reminders
- `GET /reminders/patient/{patient_id}` - Get patient reminders
- `POST /reminders/{reminder_id}/complete` - Mark reminder complete
- `GET /reminders/patient/{patient_id}/status` - Get reminder status

## Workflow

1. **Patient Registration**: Create patient record in Supabase
2. **AI Recommendation**: Generate medication schedule using AI
3. **CPC Staff Review**: Staff reviews and approves recommendations
4. **Reminder Creation**: System creates reminders for approved medications
5. **Patient Notifications**: Flutter app shows reminders and tracks compliance
6. **Optimization Status**: System determines surgery readiness

## Database Schema (Firebase Firestore)

### Core Collections
- **users**: User accounts with roles (patient, cpc_staff, admin)
- **patients**: Patient information linked to users
- **surgeries**: Surgery details and dates
- **model_recommendations**: AI-generated recommendations
- **reminders**: Medication reminders for patients

## Flutter Integration

The Flutter app can:
- Use Firebase Auth for user authentication
- Subscribe to real-time Firestore updates
- Show patient schedules and compliance status
- Receive push notifications via FCM
- Use Firebase Storage for file uploads

## MVP Features

- Simplified AI processing (rule-based for hackathon)
- Firebase real-time listeners
- Built-in authentication and authorization
- Push notifications via FCM
- No complex database setup required

## Production Considerations

For production deployment:
- Replace mock AI with real ML models
- Implement proper error handling
- Add audit logging and monitoring
- Scale Firebase plan as needed
- Add Firebase Security Rules for data protection
