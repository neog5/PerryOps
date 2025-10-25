class Reminder {
  final String patientId;
  final String medicine;
  final String action; // For medicines: Hold | Continue; others free text
  final String
  type; // medication | fasting | bathing | substance_use (optional)
  final DateTime? reminderDateTime; // preferred schedule field when present
  final DateTime scheduledDate;
  final String scheduledTime; // keep as string for display
  final String id;
  final String status; // pending/completed
  final DateTime? completedAt;
  final DateTime createdAt;

  Reminder({
    required this.patientId,
    required this.medicine,
    required this.action,
    required this.type,
    required this.reminderDateTime,
    required this.scheduledDate,
    required this.scheduledTime,
    required this.id,
    required this.status,
    required this.completedAt,
    required this.createdAt,
  });

  factory Reminder.fromJson(Map<String, dynamic> json) => Reminder(
    patientId: json['patient_id']?.toString() ?? '',
    medicine: json['medicine']?.toString() ?? '',
    action: json['action']?.toString() ?? '',
    type: json['type']?.toString() ?? '',
    reminderDateTime:
        json['reminder_datetime'] != null
            ? DateTime.tryParse(json['reminder_datetime'].toString())
            : null,
    scheduledDate:
        DateTime.tryParse(json['scheduled_date']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0),
    scheduledTime: json['scheduled_time']?.toString() ?? '',
    id: json['id']?.toString() ?? '',
    status: json['status']?.toString() ?? 'pending',
    completedAt:
        (json['completed_at'] != null)
            ? DateTime.tryParse(json['completed_at'].toString())
            : null,
    createdAt:
        DateTime.tryParse(json['created_at']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0),
  );
}

class Schedule {
  final String patientId;
  final DateTime surgeryDate;
  final List<Reminder> reminders;
  final int totalReminders;
  final int completedReminders;
  final bool isOptimized;

  Schedule({
    required this.patientId,
    required this.surgeryDate,
    required this.reminders,
    required this.totalReminders,
    required this.completedReminders,
    required this.isOptimized,
  });

  factory Schedule.fromJson(Map<String, dynamic> json) => Schedule(
    patientId: json['patient_id']?.toString() ?? '',
    surgeryDate:
        DateTime.tryParse(json['surgery_date']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0),
    reminders:
        (json['reminders'] as List<dynamic>? ?? [])
            .map((e) => Reminder.fromJson(e as Map<String, dynamic>))
            .toList(),
    totalReminders: (json['total_reminders'] as num?)?.toInt() ?? 0,
    completedReminders: (json['completed_reminders'] as num?)?.toInt() ?? 0,
    isOptimized: json['is_optimized'] == true,
  );
}
