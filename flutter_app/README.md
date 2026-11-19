# GESCO Flutter

Application scolaire locale, hors connexion, avec SQLite via Drift.

## Architecture

- lib/app : thème, navigation et interface
- lib/core : utilitaires transversaux
- lib/data/local : base SQLite et migrations
- lib/domain : règles métier et calculs indépendants de l'interface
- lib/features : écrans et modules métier

## Préparation

Installer Flutter stable et activer Windows Desktop :

```powershell
flutter doctor
flutter config --enable-windows-desktop
cd flutter_app
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter run -d windows
```

Aucun serveur, compte distant ou service cloud n'est utilisé.
