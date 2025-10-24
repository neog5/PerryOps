import 'package:flutter/material.dart';

import 'screens/landing_page.dart';
import 'screens/login_page.dart';
import 'screens/home_page.dart';
import 'models/user_type.dart';

void main() {
  runApp(const PerryOpsApp());
}

class PerryOpsApp extends StatelessWidget {
  const PerryOpsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PerryOps',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (_) => const LandingPage(),
        '/login': (_) => const LoginPage(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/home') {
          final args = settings.arguments;
          if (args is UserType) {
            return MaterialPageRoute(builder: (_) => HomePage(userType: args));
          }
          return MaterialPageRoute(builder: (_) => const LoginPage());
        }
        return null;
      },
    );
  }
}
