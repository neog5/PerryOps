# Firebase setup (Android & iOS/macOS)

This app uses Firebase Cloud Messaging (FCM) for push notifications. Platform config files must be present locally but should never be committed.

## Do not commit these files

- Android: `Frontend/perryops/android/app/google-services.json`
- iOS: `Frontend/perryops/ios/Runner/GoogleService-Info.plist`
- macOS (if used): `Frontend/perryops/macos/Runner/GoogleService-Info.plist`

These are ignored by `.gitignore` in this repo. Keep your own copies locally.

## Android

1) In Firebase Console, add an Android app with your applicationId. By default this project uses:

```
com.example.perryops
```

If you change `applicationId` in `android/app/build.gradle.kts`, regenerate the file from Firebase with the new package name.

2) Download `google-services.json` and place it at:

```
Frontend/perryops/android/app/google-services.json
```

3) Build/run:

```
flutter clean
flutter pub get
flutter run
```

Notes:
- AndroidX and Jetifier are enabled in `android/gradle.properties`.
- NDK is pinned to a version compatible with Firebase plugins.

## iOS

1) In Firebase Console, add an iOS app with your Bundle Identifier (Xcode target `Runner`).
2) Download `GoogleService-Info.plist` and add it to Xcode under `Runner` (Copy items if needed).
3) Enable capabilities in Xcode:
	 - Push Notifications
	 - Background Modes → Remote notifications

4) Run:

```
flutter clean
flutter pub get
flutter run
```

## macOS (optional)

If you plan to use macOS notifications, add a macOS app in Firebase and place its `GoogleService-Info.plist` in:

```
Frontend/perryops/macos/Runner/GoogleService-Info.plist
```

## Token registration

On successful patient login, the app retrieves an FCM token and POSTs it to your backend:

```
POST /patient/{patient_id}/register-device-token
{
	"device_token": "<FCM TOKEN>"
}
```

## Foreground/background handling

The app listens for:
- Foreground messages (in-app handling)
- Notification taps (app opened from background)
- Initial message (app opened from a terminated state)

If you want a visible banner while foregrounded, integrate `flutter_local_notifications`.

## Security notes

- Firebase keys in these files are client-side identifiers, not secrets, but restrict usage in Google Cloud where possible.
- Never commit these files. If they were accidentally committed, rotate the keys and remove them from git history (this repo has already been cleaned).

