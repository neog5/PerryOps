import 'package:flutter/material.dart';

/// Centralized design tokens and themes for the PerryOps app.
///
/// How to use:
/// - Wrap your app with MaterialApp(theme: AppTheme.lightTheme, darkTheme: AppTheme.darkTheme).
/// - Use Theme.of(context).colorScheme for colors instead of hard-coded colors.
/// - Use Theme.of(context).textTheme for text styles.
/// - Use the spacing and radius tokens in AppThemeVars for layout consistency.
class AppTheme {
  AppTheme._();

  // Brand seed color (Indigo 500). Adjust here to change the palette app-wide.
  static const Color _brandSeed = Color(0xFF3F51B5);

  static final ColorScheme _lightScheme = ColorScheme.fromSeed(
    seedColor: _brandSeed,
    brightness: Brightness.light,
  );
  static final ColorScheme _darkScheme = ColorScheme.fromSeed(
    seedColor: _brandSeed,
    brightness: Brightness.dark,
  );

  static ThemeData get lightTheme => _baseTheme(_lightScheme);
  static ThemeData get darkTheme => _baseTheme(_darkScheme);

  static ThemeData _baseTheme(ColorScheme scheme) {
    final isDark = scheme.brightness == Brightness.dark;

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      visualDensity: VisualDensity.standard,

      // Global text styles
      textTheme: Typography.material2021(
        platform: TargetPlatform.iOS,
      ).black.merge(
        const TextTheme(
          titleLarge: TextStyle(fontWeight: FontWeight.w700),
          titleMedium: TextStyle(fontWeight: FontWeight.w600),
          labelLarge: TextStyle(fontWeight: FontWeight.w600),
        ),
      ),

      // AppBar styling
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: scheme.onSurface,
          fontWeight: FontWeight.w700,
          fontSize: 20,
        ),
        iconTheme: IconThemeData(color: scheme.onSurfaceVariant),
      ),

      // Buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),

      // Text fields
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        // Slightly stronger fill in dark mode for contrast
        fillColor:
            isDark
                ? scheme.surfaceVariant.withOpacity(0.30)
                : scheme.surfaceVariant.withOpacity(0.35),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
          borderSide: BorderSide(color: scheme.primary, width: 2),
        ),
        prefixIconColor: scheme.onSurfaceVariant,
        hintStyle: TextStyle(color: scheme.onSurfaceVariant.withOpacity(0.8)),
      ),

      // Cards & list tiles
      cardTheme: CardTheme(
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
        ),
        // Avoid muddy overlays in dark mode
        surfaceTintColor: isDark ? Colors.transparent : scheme.surfaceTint,
        color: isDark ? scheme.surfaceVariant : null,
        margin: const EdgeInsets.symmetric(vertical: 6),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: scheme.onSurfaceVariant,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),

      chipTheme: ChipThemeData(
        backgroundColor: scheme.surfaceVariant,
        selectedColor: scheme.primaryContainer,
        labelStyle: TextStyle(color: scheme.onSurface),
        secondaryLabelStyle: TextStyle(color: scheme.onPrimaryContainer),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusSm),
        ),
      ),

      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: isDark ? scheme.inverseSurface : scheme.primary,
        contentTextStyle: TextStyle(
          color: isDark ? scheme.onInverseSurface : scheme.onPrimary,
        ),
        actionTextColor: scheme.secondary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppThemeVars.radiusMd),
        ),
      ),
    );
  }
}

/// Design tokens (spacing, radius) for consistent layout.
class AppThemeVars {
  AppThemeVars._();
  // Spacing (dp)
  static const double s0 = 0;
  static const double s2 = 2;
  static const double s4 = 4;
  static const double s8 = 8;
  static const double s12 = 12;
  static const double s16 = 16;
  static const double s20 = 20;
  static const double s24 = 24;
  static const double s32 = 32;
  static const double s40 = 40;

  // Radius (dp)
  static const double radiusSm = 8;
  static const double radiusMd = 12;
  static const double radiusLg = 16;
}
