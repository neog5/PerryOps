import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../models/schedule_args.dart';
import '../widgets/ui.dart';
import '../models/extract_args.dart';
import '../services/upload_service.dart';

class GenerateSchedulePage extends StatefulWidget {
  const GenerateSchedulePage({super.key, required this.args});
  final ScheduleArgs args;

  @override
  State<GenerateSchedulePage> createState() => _GenerateSchedulePageState();
}

class _GenerateSchedulePageState extends State<GenerateSchedulePage> {
  PlatformFile? _report;
  PlatformFile? _guidelines;
  bool _submitting = false;

  Future<void> _pickReport() async {
    try {
      final res = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        withData: true,
      );
      if (res != null && res.files.isNotEmpty) {
        setState(() => _report = res.files.single);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('No file selected')));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to open picker: $e')));
    }
  }

  Future<void> _pickGuidelines() async {
    try {
      final res = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        withData: true,
      );
      if (res != null && res.files.isNotEmpty) {
        setState(() => _guidelines = res.files.single);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('No file selected')));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to open picker: $e')));
    }
  }

  Future<void> _generate() async {
    if (_report == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a CPC report PDF')),
      );
      return;
    }
    setState(() => _submitting = true);
    try {
      final service = const UploadService();
      final resp = await service.upload(
        report: _report!,
        guidelines: _guidelines,
      );
      if (!mounted) return;
      // Navigate to the extract chat screen which will call the extract API
      // using the session id and display the response.
      Navigator.pushNamed(
        context,
        '/extract',
        arguments: ExtractArgs(
          sessionId: resp.sessionId,
          patientId: widget.args.patientId,
          patientName: widget.args.patientName,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to generate: $e')));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pn = widget.args.patientName ?? widget.args.patientId;
    return Scaffold(
      appBar: AppBar(title: const Text('Generate Patient schedule')),
      body: PageContainer(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    const Icon(Icons.person),
                    const SizedBox(width: 8),
                    Expanded(child: Text('Patient: $pn')),
                  ],
                ),
                const SizedBox(height: 16),
                const SectionHeader(
                  'CPC report (required)',
                  icon: Icons.picture_as_pdf,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _report != null ? _report!.name : 'No file selected',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 8),
                    OutlinedButton.icon(
                      onPressed: _submitting ? null : _pickReport,
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Choose PDF'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const SectionHeader(
                  'Updated Guidelines (optional)',
                  icon: Icons.picture_as_pdf,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _guidelines != null
                            ? _guidelines!.name
                            : 'No file selected',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 8),
                    OutlinedButton.icon(
                      onPressed: _submitting ? null : _pickGuidelines,
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Choose PDF'),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed:
                      (_report != null && !_submitting) ? _generate : null,
                  icon:
                      _submitting
                          ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                          : const Icon(Icons.playlist_add_check),
                  label: const Text('Generate schedule'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
