import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/gesco_app.dart';
import 'data/local/app_database.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final database = AppDatabase();
  runApp(ProviderScope(
    overrides: [databaseProvider.overrideWithValue(database)],
    child: const GescoApp(),
  ));
}
