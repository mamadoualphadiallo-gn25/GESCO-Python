import 'package:flutter/material.dart';

class AppTheme {
  static const navy = Color(0xFF14213D);
  static const blue = Color(0xFF356AE6);
  static const canvas = Color(0xFFF4F6FA);
  static const ink = Color(0xFF17243A);
  static const muted = Color(0xFF718096);
  static const border = Color(0xFFE5EAF2);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(seedColor: blue);
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: canvas,
      fontFamily: 'Segoe UI',
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: border),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: border)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: border)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      ),
    );
  }
}
