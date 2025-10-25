import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class PageContainer extends StatelessWidget {
  const PageContainer({super.key, required this.child, this.maxWidth = 700});
  final Widget child;
  final double maxWidth;
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppThemeVars.s24),
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: child,
        ),
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  const SectionHeader(this.text, {super.key, this.icon});
  final String text;
  final IconData? icon;
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      children: [
        if (icon != null) ...[
          Icon(icon, color: cs.primary),
          const SizedBox(width: AppThemeVars.s8),
        ],
        Text(text, style: Theme.of(context).textTheme.titleMedium),
      ],
    );
  }
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.title, this.subtitle, this.icon});
  final String title;
  final String? subtitle;
  final IconData? icon;
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppThemeVars.s16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (icon != null) ...[
              Icon(icon),
              const SizedBox(width: AppThemeVars.s12),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  if (subtitle != null) ...[
                    const SizedBox(height: AppThemeVars.s8),
                    Text(subtitle!),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
