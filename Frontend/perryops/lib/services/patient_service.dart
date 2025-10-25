import 'dart:convert';

import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:http/http.dart' as http;

import '../models/patient.dart';

class PatientService {
  const PatientService({String? baseUrl}) : _baseUrl = baseUrl;

  final String? _baseUrl;

  String _resolveBaseUrl() {
    // Use Android emulator host mapping if running on Android
    final host =
        (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
            ? '10.8.29.210'
            : 'localhost';
    return _baseUrl ?? 'http://$host:8000';
  }

  Future<List<Patient>> fetchPatients() async {
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
  }
}
