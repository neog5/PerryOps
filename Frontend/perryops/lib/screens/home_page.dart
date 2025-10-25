import 'package:flutter/material.dart';
import '../models/user_type.dart';
import '../models/patient.dart';
import '../services/patient_service.dart';
import '../models/schedule_args.dart';
import '../widgets/ui.dart';

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.userType,
    this.userName,
    this.userId,
  });

  final UserType userType;
  final String? userName;
  final String? userId;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _service = const PatientService();
  List<Patient> _patients = const [];
  Patient? _selectedPatient;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPatients();
  }

  Future<void> _loadPatients() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _service.fetchPatients();
      if (!mounted) return;
      setState(() {
        _patients = data;
        if (_patients.isEmpty) _selectedPatient = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Failed to load patients');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openPatientSearch() async {
    final selected = await showDialog<Patient>(
      context: context,
      builder: (ctx) {
        String query = '';
        return StatefulBuilder(
          builder: (context, setLocalState) {
            final filtered =
                _patients
                    .where(
                      (p) => p.name.toLowerCase().contains(query.toLowerCase()),
                    )
                    .toList();
            return AlertDialog(
              title: const Text('Select patient'),
              content: SizedBox(
                width: 400,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.search),
                        hintText: 'Search patient',
                      ),
                      onChanged: (v) => setLocalState(() => query = v),
                    ),
                    const SizedBox(height: 12),
                    Flexible(
                      child: ListView.builder(
                        shrinkWrap: true,
                        itemCount: filtered.length,
                        itemBuilder: (context, index) {
                          final p = filtered[index];
                          return ListTile(
                            title: Text(p.name),
                            subtitle: Text(p.email),
                            onTap: () => Navigator.pop(context, p),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
              ],
            );
          },
        );
      },
    );
    if (selected != null) {
      setState(() => _selectedPatient = selected);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isStaff = widget.userType == UserType.staff;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Home - ${widget.userType.label}' +
              (widget.userName != null && widget.userName!.isNotEmpty
                  ? ' · ${widget.userName}'
                  : ''),
        ),
        actions: [
          IconButton(
            tooltip: 'Change user type',
            onPressed:
                () => Navigator.pushNamedAndRemoveUntil(
                  context,
                  '/login',
                  (route) => false,
                ),
            icon: const Icon(Icons.switch_account),
          ),
        ],
      ),
      body: PageContainer(
        maxWidth: 700,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            if (widget.userName != null && widget.userName!.isNotEmpty) ...[
              Card(
                child: ListTile(
                  leading: const Icon(Icons.person),
                  title: Text('Hello, ${widget.userName}!'),
                  subtitle: Text(widget.userType.label),
                ),
              ),
              const SizedBox(height: 12),
            ],
            if (isStaff) ...[
              if (_loading) ...[
                const Center(child: CircularProgressIndicator()),
              ] else if (_error != null) ...[
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                    IconButton(
                      onPressed: _loadPatients,
                      icon: const Icon(Icons.refresh),
                      tooltip: 'Retry',
                    ),
                  ],
                ),
                const SizedBox(height: 8),
              ] else ...[
                const SectionHeader('Select patient', icon: Icons.people),
                const SizedBox(height: 8),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        OutlinedButton.icon(
                          onPressed: _openPatientSearch,
                          icon: const Icon(Icons.search),
                          label: const Text('Search patients'),
                        ),
                        if (_selectedPatient != null) ...[
                          const SizedBox(height: 12),
                          ListTile(
                            leading: const Icon(Icons.person),
                            title: Text(_selectedPatient!.name),
                            subtitle: Text(_selectedPatient!.email),
                            trailing: IconButton(
                              tooltip: 'Clear',
                              icon: const Icon(Icons.close),
                              onPressed:
                                  () => setState(() => _selectedPatient = null),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                if (_selectedPatient == null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Please select a patient to continue',
                    style: Theme.of(
                      context,
                    ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                ],
                const SizedBox(height: 16),
                _ActionCard(
                  title: 'Generate Patient schedule',
                  icon: Icons.upload_file,
                  enabled: _selectedPatient != null,
                  onTap: () {
                    if (_selectedPatient == null) return;
                    Navigator.pushNamed(
                      context,
                      '/generate',
                      arguments: ScheduleArgs(
                        patientId: _selectedPatient!.id,
                        patientName: _selectedPatient!.name,
                      ),
                    );
                  },
                ),
                const SizedBox(height: 12),
                _ActionCard(
                  title: 'View guidelines (PDF)',
                  icon: Icons.picture_as_pdf,
                  enabled: _selectedPatient != null,
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          'Fetching guidelines from backend coming soon',
                        ),
                      ),
                    );
                  },
                ),
              ],
            ] else ...[
              const SectionHeader('Quick actions', icon: Icons.bolt),
              const SizedBox(height: 8),
              _ActionCard(
                title: 'View schedule',
                icon: Icons.calendar_today,
                onTap: () {
                  if (widget.userId == null || widget.userId!.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Missing patient id')),
                    );
                    return;
                  }
                  Navigator.pushNamed(
                    context,
                    '/schedule',
                    arguments: ScheduleArgs(
                      patientId: widget.userId!,
                      patientName: widget.userName,
                    ),
                  );
                },
              ),
              const SizedBox(height: 12),
              _ActionCard(
                title: 'Upcoming reminders',
                icon: Icons.notifications_active,
                onTap: () {
                  if (widget.userId == null || widget.userId!.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Missing patient id')),
                    );
                    return;
                  }
                  Navigator.pushNamed(
                    context,
                    '/upcoming',
                    arguments: ScheduleArgs(
                      patientId: widget.userId!,
                      patientName: widget.userName,
                    ),
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.title,
    required this.icon,
    required this.onTap,
    this.enabled = true,
  });

  final String title;
  final IconData icon;
  final VoidCallback onTap;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(title),
        trailing: const Icon(Icons.chevron_right),
        enabled: enabled,
        onTap: enabled ? onTap : null,
      ),
    );
  }
}
