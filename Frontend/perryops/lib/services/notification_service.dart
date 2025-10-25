import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:permission_handler/permission_handler.dart';

/// Background message handler must be a top-level function.
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Ensure Firebase is initialized in background isolates
  try {
    await Firebase.initializeApp();
  } catch (_) {}
  // You can add background handling logic here if needed.
}

class NotificationService {
  static const _prefsKeyLastToken = 'last_fcm_token';

  const NotificationService();

  Future<void> init() async {
    await Firebase.initializeApp();

    // iOS/macOS: request permissions
    await _requestPermissions();

    // Foreground presentation (Apple platforms)
    await FirebaseMessaging.instance
        .setForegroundNotificationPresentationOptions(
          alert: true,
          badge: true,
          sound: true,
        );

    // Background handler
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

    // Persist latest token on refresh
    FirebaseMessaging.instance.onTokenRefresh.listen((t) async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefsKeyLastToken, t);
    });

    // Foreground message listener
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('FCM foreground message: ${message.messageId}');
      if (message.notification != null) {
        debugPrint(
          'Notification -> title: ${message.notification!.title}, body: ${message.notification!.body}',
        );
      }
      // Consider integrating flutter_local_notifications to show a banner while app is open.
    });

    // When a notification is tapped and opens the app (from background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('FCM opened app from background: ${message.messageId}');
      // TODO: route/navigation handling can be added here based on message.data
    });
  }

  Future<void> _requestPermissions() async {
    if (defaultTargetPlatform == TargetPlatform.iOS ||
        defaultTargetPlatform == TargetPlatform.macOS) {
      await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      // Android 13+ requires POST_NOTIFICATIONS runtime permission.
      // This will no-op on older Android versions.
      final status = await Permission.notification.status;
      if (!status.isGranted) {
        await Permission.notification.request();
      }
    }
  }

  /// Returns the current FCM token if available; falls back to last saved token.
  Future<String> getOrCreateDeviceToken() async {
    String? token;
    try {
      token = await FirebaseMessaging.instance.getToken();
    } catch (_) {}
    if (token != null && token.isNotEmpty) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefsKeyLastToken, token);
      return token;
    }
    final prefs = await SharedPreferences.getInstance();
    final last = prefs.getString(_prefsKeyLastToken);
    if (last != null && last.isNotEmpty) return last;
    // If no token yet, return empty; caller may retry later.
    return '';
  }

  /// Stream of foreground messages.
  Stream<RemoteMessage> foregroundMessages() => FirebaseMessaging.onMessage;

  /// Stream when a user taps a notification to open the app (from background).
  Stream<RemoteMessage> openedAppMessages() =>
      FirebaseMessaging.onMessageOpenedApp;

  /// Returns the message that opened the app from a terminated state, if any.
  Future<RemoteMessage?> getInitialMessage() =>
      FirebaseMessaging.instance.getInitialMessage();
}
