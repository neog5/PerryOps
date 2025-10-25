import 'package:flutter/material.dart';
import '../models/schedule_args.dart';
import '../models/schedule.dart';
import '../services/schedule_service.dart';
import '../widgets/ui.dart';

class SchedulePage extends StatefulWidget {
  const SchedulePage({super.key, required this.args});
  final ScheduleArgs args;

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  final _service = const ScheduleService();
  Schedule? _schedule;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final s = await _service.fetchSchedule(widget.args.patientId);
      if (!mounted) return;
      setState(() => _schedule = s);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title =
        widget.args.patientName != null
            ? 'Schedule · ${widget.args.patientName}'
            : 'Schedule';
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: PageContainer(
        child:
            _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                ? _ErrorView(message: _error!, onRetry: _load)
                : _schedule == null
                ? const Center(child: Text('No data'))
                : _ScheduleView(schedule: _schedule!),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 8),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

class _ScheduleView extends StatelessWidget {
  const _ScheduleView({required this.schedule});
  final Schedule schedule;

  @override
  Widget build(BuildContext context) {
    final meds =
        schedule.reminders
            .where(
              (r) => r.medicine.trim().isNotEmpty || r.type == 'medication',
            )
            .toList();
    final substance =
        schedule.reminders
            .where((r) => r.type.toLowerCase() == 'substance_use')
            .toList();
    final fasting =
        schedule.reminders
            .where((r) => r.type.toLowerCase() == 'fasting')
            .toList();
    final bathing =
        schedule.reminders
            .where((r) => r.type.toLowerCase() == 'bathing')
            .toList();

    return ListView(
      padding: const EdgeInsets.all(0),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.local_hospital),
            title: const Text('Surgery date'),
            subtitle: Builder(
              builder: (context) {
                final d = schedule.surgeryDate.toLocal();
                final date = _formatDate(d);
                final time = _formatHour(d);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [Text(date), Text(time)],
                );
              },
            ),
            trailing: Tooltip(
              message: schedule.isOptimized ? 'Optimized' : 'Not optimized',
              child: Icon(
                schedule.isOptimized ? Icons.check_circle : Icons.info_outline,
                color: schedule.isOptimized ? Colors.green : Colors.orange,
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        _Section(
          title: 'Medicines',
          icon: Icons.medication,
          children: meds.map(_medTile).toList(),
        ),
        const SizedBox(height: 12),
        _Section(
          title: 'Substance use',
          icon: Icons.no_drinks,
          children: substance.map(_substanceTile).toList(),
        ),
        const SizedBox(height: 12),
        _Section(
          title: 'Fasting',
          icon: Icons.fastfood,
          children: fasting.map(_simpleTile).toList(),
        ),
        const SizedBox(height: 12),
        _Section(
          title: 'Bathing',
          icon: Icons.shower,
          children: bathing.map(_simpleTile).toList(),
        ),
      ],
    );
  }

  Widget _medTile(Reminder r) {
    final isHold = r.action.toLowerCase().contains('hold');
    final actionLabel =
        isHold
            ? 'Hold'
            : (r.action.toLowerCase().contains('continue')
                ? 'Continue'
                : r.action);
    final dt = r.reminderDateTime;

    return Card(
      child: ListTile(
        title: Text(r.medicine),
        subtitle:
            dt == null
                ? null
                : Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatDate(dt.toLocal())),
                    const SizedBox(width: 16),
                    const Icon(Icons.access_time, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatHour(dt.toLocal())),
                  ],
                ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: isHold ? Colors.red.shade600 : Colors.green.shade600,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            actionLabel,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }

  Widget _simpleTile(Reminder r) {
    final dt = r.reminderDateTime;
    return Card(
      child: ListTile(
        title: Text(r.action.isNotEmpty ? r.action : 'Reminder'),
        subtitle:
            dt == null
                ? null
                : Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatDate(dt.toLocal())),
                    const SizedBox(width: 16),
                    const Icon(Icons.access_time, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatHour(dt.toLocal())),
                  ],
                ),
      ),
    );
  }

  Widget _substanceTile(Reminder r) {
    final dt = r.reminderDateTime;
    return Card(
      child: ListTile(
        title: Text(r.action.isNotEmpty ? r.action : 'Substance use'),
        subtitle:
            dt == null
                ? null
                : Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatDate(dt.toLocal())),
                    const SizedBox(width: 16),
                    const Icon(Icons.access_time, size: 16),
                    const SizedBox(width: 6),
                    Text(_formatHour(dt.toLocal())),
                  ],
                ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.red.shade600,
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Text(
            'Avoid',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }

  // Deprecated: previously used scheduledDate/scheduledTime; replaced by reminderDateTime when present

  String _formatDate(DateTime d) {
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${d.day} ${months[(d.month - 1).clamp(0, 11)]} ${d.year}';
  }

  String _formatHour(DateTime d) {
    final hour24 = d.hour;
    final isPm = hour24 >= 12;
    var hour12 = hour24 % 12;
    if (hour12 == 0) hour12 = 12;
    return '${hour12}${isPm ? 'pm' : 'am'}';
  }
}

class _Section extends StatelessWidget {
  const _Section({
    required this.title,
    required this.icon,
    required this.children,
  });
  final String title;
  final IconData icon;
  final List<Widget> children;
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon),
            const SizedBox(width: 6),
            Text(title, style: Theme.of(context).textTheme.titleMedium),
          ],
        ),
        const SizedBox(height: 8),
        if (children.isEmpty)
          const Text('No items', style: TextStyle(color: Colors.grey))
        else
          ...children,
      ],
    );
  }
}

// Removed _StatChip; summary chips are no longer displayed
