import 'package:flutter/material.dart';
import '../models/user_type.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.userType});

  final UserType userType;

  @override
  Widget build(BuildContext context) {
    final isStaff = userType == UserType.staff;
    return Scaffold(
      appBar: AppBar(
        title: Text('Home - ${userType.label}'),
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
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                if (isStaff) ...[
                  _ActionCard(
                    title: 'Upload CPC report',
                    icon: Icons.upload_file,
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Upload flow coming soon'),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 12),
                  _ActionCard(
                    title: 'View guidelines (PDF)',
                    icon: Icons.picture_as_pdf,
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
                ] else ...[
                  _ActionCard(
                    title: 'View schedule',
                    icon: Icons.calendar_today,
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Schedule view coming soon'),
                        ),
                      );
                    },
                  ),
                ],
              ],
            ),
          ),
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
  });

  final String title;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(title),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
