import 'dart:convert';

import 'package:http/http.dart' as http;

class CheckComplianceService {
  const CheckComplianceService({this.baseUrl = 'http://10.8.97.24:8000'});

  final String baseUrl;

  Future<ComplianceResponse> check({
    required String sessionId,
    String complianceModel = 'amsaravi/medgemma-4b-it:q8',
  }) async {
    final uri = Uri.parse('$baseUrl/api/check-compliance');
    final resp = await http
        .post(
          uri,
          headers: {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: {'session_id': sessionId, 'compliance_model': complianceModel},
        )
        .timeout(const Duration(seconds: 60));

    if (resp.statusCode < 200 || resp.statusCode >= 300) {
      throw Exception('Check compliance failed (HTTP ${resp.statusCode})');
    }
    return ComplianceResponse.parse(resp.body);
  }
}

class ComplianceResponse {
  final String rawBody;
  final Map<String, dynamic>? json;
  final String displayText;

  ComplianceResponse({
    required this.rawBody,
    required this.json,
    required this.displayText,
  });

  factory ComplianceResponse.parse(String body) {
    Map<String, dynamic>? parsed;
    String text = body;
    try {
      parsed = jsonDecode(body) as Map<String, dynamic>;
      final candidates = [
        'result',
        'message',
        'text',
        'content',
        'summary',
        'compliance',
        'data',
      ];
      for (final key in candidates) {
        final v = parsed[key];
        if (v is String && v.trim().isNotEmpty) {
          text = v;
          break;
        }
        if (v is List) {
          text = v.map((e) => e.toString()).join('\n');
          break;
        }
      }
    } catch (_) {
      parsed = null;
      text = body;
    }
    return ComplianceResponse(rawBody: body, json: parsed, displayText: text);
  }
}
