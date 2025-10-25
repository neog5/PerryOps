import 'package:flutter/material.dart';
import '../models/extract_args.dart';
import '../services/extract_service.dart';
import '../services/check_compliance_service.dart';
import '../services/merge_service.dart';
import '../widgets/ui.dart';

class ExtractChatPage extends StatefulWidget {
  const ExtractChatPage({super.key, required this.args});
  final ExtractArgs args;

  @override
  State<ExtractChatPage> createState() => _ExtractChatPageState();
}

class _ExtractChatPageState extends State<ExtractChatPage> {
  bool _loading = true;
  String? _error;
  final List<_Message> _messages = [];
  final TextEditingController _controller = TextEditingController();
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _runFlow();
  }

  Future<void> _runFlow() async {
    setState(() {
      _loading = true;
      _error = null;
      _messages.clear();
    });
    try {
      // Step 1: extract
      final extractService = const ExtractService();
      await extractService.extract(sessionId: widget.args.sessionId);

      // Step 2: check compliance (display this)
      final ccService = const CheckComplianceService();
      final cc = await ccService.check(sessionId: widget.args.sessionId);
      if (!mounted) return;
      setState(() {
        final text =
            cc.displayText.isNotEmpty
                ? cc.displayText
                : (cc.json != null ? cc.json.toString() : cc.rawBody);
        _messages.add(_Message.assistant(text));
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _send() async {
    if (_sending) return;
    final input = _controller.text.trim();
    setState(() => _sending = true);
    try {
      if (input.isNotEmpty) {
        setState(() => _messages.add(_Message.user(input)));
      }
      final corrections =
          input.isEmpty
              ? <String, dynamic>{}
              : <String, dynamic>{'additionalProp': input};
      final service = const MergeService();
      final resp = await service.merge(
        sessionId: widget.args.sessionId,
        corrections: corrections,
      );
      if (!mounted) return;
      final text =
          resp.displayText.isNotEmpty
              ? resp.displayText
              : (resp.json != null ? resp.json.toString() : resp.rawBody);
      setState(() {
        _messages.add(_Message.assistant(text));
        _controller.clear();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(_Message.assistant('Merge failed: $e'));
      });
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pn = widget.args.patientName ?? widget.args.patientId;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Schedule generation'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(24),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Text(
              'Patient: $pn',
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: Colors.white70),
            ),
          ),
        ),
      ),
      body: PageContainer(
        maxWidth: 800,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 12),
            Expanded(
              child:
                  _loading
                      ? const _LoadingView()
                      : _error != null
                      ? _ErrorView(error: _error!, onRetry: _runFlow)
                      : _ChatList(messages: _messages),
            ),
            const SizedBox(height: 8),
            _InputBar(
              controller: _controller,
              onSend: _send,
              sending: _sending,
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatList extends StatelessWidget {
  const _ChatList({required this.messages});
  final List<_Message> messages;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final m = messages[index];
        final align =
            m.role == _Role.assistant
                ? Alignment.centerLeft
                : Alignment.centerRight;
        final color =
            m.role == _Role.assistant
                ? Theme.of(context).colorScheme.surfaceContainerHigh
                : Theme.of(context).colorScheme.primaryContainer;
        return Align(
          alignment: align,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(m.text, style: Theme.of(context).textTheme.bodyMedium),
          ),
        );
      },
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error, required this.onRetry});
  final String error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.error_outline, color: Colors.red),
          const SizedBox(height: 8),
          Text(
            error,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: Colors.red),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}

class _LoadingView extends StatelessWidget {
  const _LoadingView();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const CircularProgressIndicator(),
        const SizedBox(height: 12),
        Text(
          'Generating and checking compliance... This may take a moment.',
          style: Theme.of(context).textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

enum _Role { user, assistant }

class _Message {
  final _Role role;
  final String text;
  const _Message(this.role, this.text);
  factory _Message.user(String text) => _Message(_Role.user, text);
  factory _Message.assistant(String text) => _Message(_Role.assistant, text);
}

class _InputBar extends StatelessWidget {
  const _InputBar({
    required this.controller,
    required this.onSend,
    required this.sending,
  });
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool sending;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Type corrections (optional)...',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              minLines: 1,
              maxLines: 4,
            ),
          ),
          const SizedBox(width: 8),
          FilledButton.icon(
            onPressed: sending ? null : onSend,
            icon:
                sending
                    ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                    : const Icon(Icons.send),
            label: const Text('Send'),
          ),
        ],
      ),
    );
  }
}
