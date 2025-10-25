import 'dart:convert';

import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:http/http.dart' as http;

import '../models/auth_response.dart';

class AuthService {
  const AuthService({String? baseUrl}) : _baseUrl = baseUrl;

  final String? _baseUrl;

  String _resolveBaseUrl() {
    final host =
        (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
            ? '10.8.29.210'
            : 'localhost';
    return _baseUrl ?? 'http://$host:8000';
  }

  Future<AuthResponse> loginCpc(String email, String password) async {
    return _login('/cpc/login', email, password);
  }

  Future<AuthResponse> loginPatient(String email, String password) async {
    return _login('/patient/login', email, password);
  }

  Future<AuthResponse> _login(
    String path,
    String email,
    String password,
  ) async {
    final uri = Uri.parse('${_resolveBaseUrl()}$path');
    final resp = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));

    if (resp.statusCode == 200 || resp.statusCode == 201) {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return AuthResponse.fromJson(body);
    }

    try {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      final apiErr = ApiError.fromJson(body);
      throw ApiException(apiErr.message());
    } catch (_) {
      throw ApiException('Login failed (HTTP ${resp.statusCode})');
    }
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}
