// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:perryops/main.dart';

void main() {
  testWidgets('Landing to Login navigation', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const PerryOpsApp());

    // Landing page should show Get Started button
    expect(find.text('Get Started'), findsOneWidget);

    // Navigate to Login
    await tester.tap(find.text('Get Started'));
    await tester.pumpAndSettle();

    // On Login page, confirm title
    expect(find.text('Login'), findsOneWidget);
    expect(find.text('Staff (CPC Staff)'), findsOneWidget);
    expect(find.text('Patient'), findsOneWidget);
  });
}
