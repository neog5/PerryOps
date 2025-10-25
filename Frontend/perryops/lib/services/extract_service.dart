import 'dart:convert';

import 'package:http/http.dart' as http;

class ExtractService {
  const ExtractService({this.baseUrl = 'http://10.8.97.24:8000'});

  final String baseUrl;

  Future<ExtractResponse> extract({
    required String sessionId,
    String model = 'qwen32b',
  }) async {
    final uri = Uri.parse('$baseUrl/api/extract');
    final resp = await http
        .post(
          uri,
          headers: {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: {'session_id': sessionId, 'model': model},
        )
        .timeout(const Duration(seconds: 30));

    if (resp.statusCode < 200 || resp.statusCode >= 300) {
      throw Exception('Extract failed (HTTP ${resp.statusCode})');
    }

    return ExtractResponse.parse(resp.body);
  }
}

class ExtractResponse {
  final String rawBody;
  final Map<String, dynamic>? json;
  final String displayText;

  ExtractResponse({
    required this.rawBody,
    required this.json,
    required this.displayText,
  });

  factory ExtractResponse.parse(String body) {
    Map<String, dynamic>? parsed;
    String text = body;
    try {
      parsed = jsonDecode(body) as Map<String, dynamic>;
      // Heuristics for a main text field
      final candidates = [
        'result',
        'message',
        'text',
        'content',
        'summary',
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
    return ExtractResponse(rawBody: body, json: parsed, displayText: text);
  }
}
