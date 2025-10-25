import 'dart:convert';

import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:http/http.dart' as http;

import '../models/schedule.dart';
import '../services/auth_service.dart';
import '../models/auth_response.dart';
import '../models/upcoming_reminder.dart';

class ScheduleService {
  const ScheduleService({String? baseUrl}) : _baseUrl = baseUrl;

  final String? _baseUrl;

  String _resolveBaseUrl() {
    final host =
        (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
            ? '10.8.29.210'
            : 'localhost';
    return _baseUrl ?? 'http://$host:8000';
  }

  // Some patient userIds come prefixed with 'user_'.
  // Backend expects the raw patient id (e.g., 'patient_001').
  String _normalizePatientId(String id) {
    return id.startsWith('user_') ? id.substring(5) : id;
  }

  Future<Schedule> fetchSchedule(String patientId) async {
    final normalizedId = _normalizePatientId(patientId);
    final uri = Uri.parse(
      '${_resolveBaseUrl()}/patient/$normalizedId/schedule',
    );
    final resp = await http.get(uri).timeout(const Duration(seconds: 10));
    if (resp.statusCode != 200) {
      try {
        final body = jsonDecode(resp.body) as Map<String, dynamic>;
        final apiErr = ApiError.fromJson(body);
        throw ApiException(apiErr.message());
      } catch (_) {
        throw ApiException('Failed to load schedule (HTTP ${resp.statusCode})');
      }
    }
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    return Schedule.fromJson(body);
  }

  Future<UpcomingReminders> fetchUpcomingReminders(
    String patientId, {
    int hoursAhead = 1000,
  }) async {
    final normalizedId = _normalizePatientId(patientId);
    final uri = Uri.parse(
      '${_resolveBaseUrl()}/patient/$normalizedId/upcoming-reminders',
    ).replace(queryParameters: {'hours_ahead': hoursAhead.toString()});
    final resp = await http.get(uri).timeout(const Duration(seconds: 10));
    if (resp.statusCode != 200) {
      try {
        final body = jsonDecode(resp.body) as Map<String, dynamic>;
        final apiErr = ApiError.fromJson(body);
        throw ApiException(apiErr.message());
      } catch (_) {
        throw ApiException(
          'Failed to load upcoming reminders (HTTP ${resp.statusCode})',
        );
      }
    }
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    return UpcomingReminders.fromJson(body);
  }
}
