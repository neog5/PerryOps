import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:file_picker/file_picker.dart';

class UploadService {
  const UploadService({this.baseUrl = 'http://10.8.97.24:8000'});

  final String baseUrl;

  Future<UploadResponse> upload({
    required PlatformFile report,
    PlatformFile? guidelines,
  }) async {
    final uri = Uri.parse('$baseUrl/api/upload');
    final req = http.MultipartRequest('POST', uri);

    // Report (required)
    if (report.path != null && report.path!.isNotEmpty) {
      req.files.add(
        await http.MultipartFile.fromPath(
          'report',
          report.path!,
          contentType: MediaType('application', 'pdf'),
          filename: report.name,
        ),
      );
    } else if (report.bytes != null) {
      req.files.add(
        http.MultipartFile.fromBytes(
          'report',
          report.bytes!,
          contentType: MediaType('application', 'pdf'),
          filename: report.name.isNotEmpty ? report.name : 'report.pdf',
        ),
      );
    } else {
      throw Exception('Invalid report file');
    }

    // Guidelines (optional)
    if (guidelines != null) {
      if (guidelines.path != null && guidelines.path!.isNotEmpty) {
        req.files.add(
          await http.MultipartFile.fromPath(
            'guidelines',
            guidelines.path!,
            contentType: MediaType('application', 'pdf'),
            filename: guidelines.name,
          ),
        );
      } else if (guidelines.bytes != null) {
        req.files.add(
          http.MultipartFile.fromBytes(
            'guidelines',
            guidelines.bytes!,
            contentType: MediaType('application', 'pdf'),
            filename:
                guidelines.name.isNotEmpty ? guidelines.name : 'guidelines.pdf',
          ),
        );
      }
    }

    req.headers['accept'] = 'application/json';

    final streamed = await req.send().timeout(const Duration(seconds: 30));
    final resp = await http.Response.fromStream(streamed);
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw Exception('Upload failed (HTTP ${resp.statusCode})');
    }
    return UploadResponse.fromJson(resp.body);
  }
}

class UploadResponse {
  final String sessionId;
  final String message;
  final List<String> filesUploaded;

  UploadResponse({
    required this.sessionId,
    required this.message,
    required this.filesUploaded,
  });

  factory UploadResponse.fromJson(String body) {
    final Map<String, dynamic> json =
        (body.isNotEmpty ? (jsonDecode(body) as Map<String, dynamic>) : {});
    return UploadResponse(
      sessionId: json['session_id']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      filesUploaded:
          (json['files_uploaded'] as List<dynamic>? ?? [])
              .map((e) => e.toString())
              .toList(),
    );
  }
}
