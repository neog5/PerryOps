import 'package:flutter/material.dart';
import '../widgets/ui.dart';

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PerryOps')),
      body: PageContainer(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(
              Icons.local_hospital,
              size: 56,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 12),
            Text(
              'Welcome to PerryOps',
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Streamlined CPC reporting and patient scheduling.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            const InfoCard(
              title: 'For staff',
              subtitle: 'Upload CPC reports and access clinical guidelines.',
              icon: Icons.badge,
            ),
            const InfoCard(
              title: 'For patients',
              subtitle: 'View upcoming reminders and pre-op schedule.',
              icon: Icons.event_available,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => Navigator.pushNamed(context, '/login'),
              child: const Text('Get Started'),
            ),
          ],
        ),
      ),
    );
  }
}
