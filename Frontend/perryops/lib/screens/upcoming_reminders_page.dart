import 'package:flutter/material.dart';
import '../models/schedule_args.dart';
import '../models/upcoming_reminder.dart';
import '../services/schedule_service.dart';
import '../widgets/ui.dart';

class UpcomingRemindersPage extends StatefulWidget {
  const UpcomingRemindersPage({super.key, required this.args});
  final ScheduleArgs args;

  @override
  State<UpcomingRemindersPage> createState() => _UpcomingRemindersPageState();
}

class _UpcomingRemindersPageState extends State<UpcomingRemindersPage> {
  final _service = const ScheduleService();
  UpcomingReminders? _data;
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
      final s = await _service.fetchUpcomingReminders(widget.args.patientId);
      if (!mounted) return;
      setState(() => _data = s);
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
            ? 'Upcoming · ${widget.args.patientName}'
            : 'Upcoming reminders';
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
                : _data == null
                ? const Center(child: Text('No data'))
                : _UpcomingView(data: _data!),
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

class _UpcomingView extends StatelessWidget {
  const _UpcomingView({required this.data});
  final UpcomingReminders data;

  @override
  Widget build(BuildContext context) {
    final reminders = [...data.reminders]
      ..sort((a, b) => a.reminderDateTime.compareTo(b.reminderDateTime));
    return ListView.builder(
      padding: const EdgeInsets.all(0),
      itemCount: reminders.length,
      itemBuilder: (context, index) {
        final r = reminders[index];
        return Card(
          child: ListTile(
            leading: Icon(
              _iconFor(r),
              color: Theme.of(context).colorScheme.primary,
            ),
            title: Text(_lineText(r)),
          ),
        );
      },
    );
  }

  IconData _iconFor(UpcomingReminder r) {
    switch (r.type.toLowerCase()) {
      case 'medication':
        return Icons.medication;
      case 'bathing':
        return Icons.shower;
      case 'fasting':
        return Icons.fastfood;
      case 'substance_use':
        return Icons.no_drinks;
      default:
        return Icons.schedule;
    }
  }

  String _lineText(UpcomingReminder r) {
    final when = _formatDateTime(r);
    final type = r.type.toLowerCase();
    if (type == 'medication') {
      final med = (r.medicine ?? '').trim();
      final isStop =
          r.action.toLowerCase().contains('hold') ||
          r.action.toLowerCase().contains('stop');
      final verb = isStop ? 'Stop' : 'Take';
      return med.isNotEmpty
          ? "$verb '$med' at $when"
          : '$verb medicine at $when';
    }
    if (type == 'bathing') {
      return 'Bath at $when';
    }
    if (type == 'fasting') {
      final isStart = r.action.toLowerCase().contains('start');
      return isStart ? 'Start fasting at $when' : 'Fasting at $when';
    }
    if (type == 'substance_use') {
      if (r.action.toLowerCase().contains('alcohol')) {
        return 'Avoid alcohol at $when';
      }
      return 'Avoid substances at $when';
    }
    return 'Reminder at $when';
  }

  String _formatDateTime(UpcomingReminder r) {
    final d = r.reminderDateTime.toLocal();
    final date =
        '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    final time =
        '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    return '$date • $time';
  }
}
