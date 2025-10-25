class Patient {
  final String userId;
  final String name;
  final String email;
  final String phone;
  final String condition;
  final String id;
  final DateTime createdAt;

  const Patient({
    required this.userId,
    required this.name,
    required this.email,
    required this.phone,
    required this.condition,
    required this.id,
    required this.createdAt,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      userId: json['user_id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      phone: json['phone']?.toString() ?? '',
      condition: json['condition']?.toString() ?? '',
      id: json['id']?.toString() ?? '',
      createdAt:
          DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
    );
  }

  @override
  String toString() => name.isNotEmpty ? name : email;

  @override
  bool operator ==(Object other) => other is Patient && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
