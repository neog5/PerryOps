class UpcomingReminder {
  final String id;
  final String patientId;
  final String status; // e.g., pending/completed
  final String type; // medication | fasting | bathing | substance_use
  final String action; // e.g., hold, start_fasting, special_bath, avoid_alcohol
  final DateTime reminderDateTime;
  final DateTime createdAt;
  final String? medicine; // only for medication
  final String? notes;

  UpcomingReminder({
    required this.id,
    required this.patientId,
    required this.status,
    required this.type,
    required this.action,
    required this.reminderDateTime,
    required this.createdAt,
    this.medicine,
    this.notes,
  });

  factory UpcomingReminder.fromJson(Map<String, dynamic> json) =>
      UpcomingReminder(
        id: json['id']?.toString() ?? '',
        patientId: json['patient_id']?.toString() ?? '',
        status: json['status']?.toString() ?? 'pending',
        type: json['type']?.toString() ?? '',
        action: json['action']?.toString() ?? '',
        reminderDateTime:
            DateTime.tryParse(json['reminder_datetime']?.toString() ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
        createdAt:
            DateTime.tryParse(json['created_at']?.toString() ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
        medicine: json['medicine']?.toString(),
        notes: json['notes']?.toString(),
      );
}

class UpcomingReminders {
  final String patientId;
  final List<UpcomingReminder> reminders;
  final int count;

  UpcomingReminders({
    required this.patientId,
    required this.reminders,
    required this.count,
  });

  factory UpcomingReminders.fromJson(Map<String, dynamic> json) =>
      UpcomingReminders(
        patientId: json['patient_id']?.toString() ?? '',
        reminders:
            (json['upcoming_reminders'] as List<dynamic>? ?? [])
                .map(
                  (e) => UpcomingReminder.fromJson(e as Map<String, dynamic>),
                )
                .toList(),
        count: (json['count'] as num?)?.toInt() ?? 0,
      );
}
