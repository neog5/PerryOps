// import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;

import '../models/patient.dart';

class PatientService {
  const PatientService({String? baseUrl});

  // String _resolveBaseUrl() {
  //   // Use Android emulator host mapping if running on Android
  //   final host =
  //       (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
  //           ? '10.8.29.210'
  //           : 'localhost';
  //   return _baseUrl ?? 'http://$host:8000';
  // }

  Future<List<Patient>> fetchPatients() async {
    // TEMP: DB is currently down. Return mocked CPC/getpatients data.
    // To restore original behavior, remove the block below and uncomment the
    // network code further down.
    final mocked = [
      {
        "user_id": "string",
        "name": "string",
        "email": "user@example.com",
        "phone": "string",
        "condition": "string",
        "id": "O4rU7NMRbNS9in7xUX2t",
        "created_at": "2025-10-24T16:42:09.861954Z",
      },
      {
        "user_id": "user_patient_001",
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "+1-555-0101",
        "condition": "Hypertension, Diabetes",
        "id": "patient_001",
        "created_at": "2025-10-24T15:58:03.296040Z",
      },
      {
        "user_id": "user_patient_002",
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "phone": "+1-555-0102",
        "condition": "Atrial Fibrillation",
        "id": "patient_002",
        "created_at": "2025-10-24T15:58:03.296046Z",
      },
      {
        "user_id": "user_patient_003",
        "name": "Robert Wilson",
        "email": "robert.wilson@email.com",
        "phone": "+1-555-0103",
        "condition": "Coronary Artery Disease",
        "id": "patient_003",
        "created_at": "2025-10-24T15:58:03.296046Z",
      },
    ];
    return mocked.map((e) => Patient.fromJson(e)).toList();

    /* Original implementation (restore when DB is back):
    final uri = Uri.parse('${_resolveBaseUrl()}/cpc/patients');
    final resp = await http.get(uri).timeout(const Duration(seconds: 10));
    if (resp.statusCode != 200) {
      throw Exception('Failed to load patients: HTTP ${resp.statusCode}');
    }
    final body = resp.body;
    final decoded = jsonDecode(body);
    if (decoded is! List) {
      throw Exception('Unexpected response format');
    }
    return decoded
        .cast<Map<String, dynamic>>()
        .map((e) => Patient.fromJson(e))
        .toList();
    */
  }
}
