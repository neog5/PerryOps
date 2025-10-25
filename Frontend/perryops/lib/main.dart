import 'package:flutter/material.dart';
import 'services/notification_service.dart';
import 'package:firebase_core/firebase_core.dart';

import 'screens/landing_page.dart';
import 'screens/login_page.dart';
import 'screens/home_page.dart';
import 'models/user_type.dart';
import 'models/home_args.dart';
import 'screens/schedule_page.dart';
import 'models/schedule_args.dart';
import 'screens/upcoming_reminders_page.dart';
import 'screens/generate_schedule_page.dart';
import 'screens/extract_chat_page.dart';
import 'models/extract_args.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Initialize Firebase and messaging early
  try {
    await Firebase.initializeApp();
    await const NotificationService().init();
  } catch (_) {
    // If Firebase init fails (e.g., missing google-services files), continue app startup
  }
  runApp(const PerryOpsApp());
}

class PerryOpsApp extends StatelessWidget {
  const PerryOpsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PerryOps',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: '/',
      routes: {
        '/': (_) => const LandingPage(),
        '/login': (_) => const LoginPage(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/home') {
          final args = settings.arguments;
          if (args is HomeArgs) {
            return MaterialPageRoute(
              builder:
                  (_) => HomePage(
                    userType: args.userType,
                    userName: args.name,
                    userId: args.userId,
                  ),
            );
          } else if (args is UserType) {
            return MaterialPageRoute(builder: (_) => HomePage(userType: args));
          } else {
            return MaterialPageRoute(builder: (_) => const LoginPage());
          }
        }
        if (settings.name == '/schedule') {
          final args = settings.arguments;
          if (args is ScheduleArgs) {
            return MaterialPageRoute(builder: (_) => SchedulePage(args: args));
          }
          return MaterialPageRoute(builder: (_) => const LoginPage());
        }
        if (settings.name == '/generate') {
          final args = settings.arguments;
          if (args is ScheduleArgs) {
            return MaterialPageRoute(
              builder: (_) => GenerateSchedulePage(args: args),
            );
          }
          return MaterialPageRoute(builder: (_) => const LoginPage());
        }
        if (settings.name == '/upcoming') {
          final args = settings.arguments;
          if (args is ScheduleArgs) {
            return MaterialPageRoute(
              builder: (_) => UpcomingRemindersPage(args: args),
            );
          }
          return MaterialPageRoute(builder: (_) => const LoginPage());
        }
        if (settings.name == '/extract') {
          final args = settings.arguments;
          if (args is ExtractArgs) {
            return MaterialPageRoute(
              builder: (_) => ExtractChatPage(args: args),
            );
          }
          return MaterialPageRoute(builder: (_) => const LoginPage());
        }
        return null;
      },
    );
  }
}
