import 'dart:convert';

import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:http/http.dart' as http;

import 'auth_service.dart';
import '../models/auth_response.dart';

class DeviceService {
  const DeviceService({String? baseUrl}) : _baseUrl = baseUrl;

  final String? _baseUrl;

  String _resolveBaseUrl() {
    final host =
        (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
            ? '10.8.29.210'
            : 'localhost';
    return _baseUrl ?? 'http://$host:8000';
  }

  String _normalizePatientId(String id) {
    return id.startsWith('user_') ? id.substring(5) : id;
  }

  Future<String> registerDeviceToken(
    String patientId,
    String deviceToken,
  ) async {
    final normalizedId = _normalizePatientId(patientId);
    final uri = Uri.parse(
      '${_resolveBaseUrl()}/patient/$normalizedId/register-device-token',
    );
    final resp = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'device_token': deviceToken}),
        )
        .timeout(const Duration(seconds: 10));

    if (resp.statusCode == 200 || resp.statusCode == 201) {
      // API returns a success string message in the response body
      return resp.body.toString();
    }

    try {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      final apiErr = ApiError.fromJson(body);
      throw ApiException(apiErr.message());
    } catch (_) {
      throw ApiException('Failed to register device (HTTP ${resp.statusCode})');
    }
  }
}
