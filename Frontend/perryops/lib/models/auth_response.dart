class AuthResponse {
  final String userId;
  final String email;
  final String name;
  final String role;
  final String accessToken;
  final String tokenType;

  AuthResponse({
    required this.userId,
    required this.email,
    required this.name,
    required this.role,
    required this.accessToken,
    required this.tokenType,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      userId: json['user_id']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      role: json['role']?.toString() ?? '',
      accessToken: json['access_token']?.toString() ?? '',
      tokenType: json['token_type']?.toString() ?? '',
    );
  }
}

class ApiError {
  final List<Map<String, dynamic>> detail;

  ApiError(this.detail);

  factory ApiError.fromJson(Map<String, dynamic> json) {
    final d = json['detail'];
    if (d is List) {
      return ApiError(d.cast<Map<String, dynamic>>());
    }
    return ApiError([]);
  }

  String message() {
    if (detail.isEmpty) return 'Unknown error';
    final first = detail.first;
    return first['msg']?.toString() ?? 'Unknown error';
  }
}
