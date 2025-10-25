import 'dart:convert';

import 'package:http/http.dart' as http;

class MergeService {
  const MergeService({this.baseUrl = 'http://10.8.97.24:8000'});

  final String baseUrl;

  Future<MergeResponse> merge({
    required String sessionId,
    Map<String, dynamic>? corrections,
  }) async {
    final uri = Uri.parse('$baseUrl/api/merge');
    final body = jsonEncode({
      'session_id': sessionId,
      'corrections': corrections ?? <String, dynamic>{},
    });
    final resp = await http
        .post(
          uri,
          headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: body,
        )
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode < 200 || resp.statusCode >= 300) {
      throw Exception('Merge failed (HTTP ${resp.statusCode})');
    }
    return MergeResponse.parse(resp.body);
  }
}

class MergeResponse {
  final String rawBody;
  final Map<String, dynamic>? json;
  final String displayText;

  MergeResponse({
    required this.rawBody,
    required this.json,
    required this.displayText,
  });

  factory MergeResponse.parse(String body) {
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
    return MergeResponse(rawBody: body, json: parsed, displayText: text);
  }
}
