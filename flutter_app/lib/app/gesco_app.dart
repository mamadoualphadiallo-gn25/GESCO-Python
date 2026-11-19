import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/local/app_database.dart';
import 'theme/app_theme.dart';

class GescoApp extends StatelessWidget {
  const GescoApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'GESCO',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light,
    home: const DashboardScreen(),
  );
}

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(databaseProvider);
    return Scaffold(
      body: Row(children: [
        NavigationRail(
          extended: MediaQuery.sizeOf(context).width > 1050,
          backgroundColor: AppTheme.navy,
          selectedIndex: 0,
          onDestinationSelected: (_) {},
          leading: const Padding(
            padding: EdgeInsets.symmetric(vertical: 28),
            child: Column(children: [
              Icon(Icons.school_rounded, color: Colors.white, size: 34),
              SizedBox(height: 8),
              Text('GESCO', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
            ]),
          ),
          destinations: const [
            NavigationRailDestination(icon: Icon(Icons.dashboard_outlined), label: Text('Tableau de bord')),
            NavigationRailDestination(icon: Icon(Icons.people_outline), label: Text('Élèves')),
            NavigationRailDestination(icon: Icon(Icons.meeting_room_outlined), label: Text('Classes')),
            NavigationRailDestination(icon: Icon(Icons.menu_book_outlined), label: Text('Matières')),
            NavigationRailDestination(icon: Icon(Icons.edit_note_outlined), label: Text('Notes')),
            NavigationRailDestination(icon: Icon(Icons.leaderboard_outlined), label: Text('Classements')),
            NavigationRailDestination(icon: Icon(Icons.description_outlined), label: Text('Bulletins')),
            NavigationRailDestination(icon: Icon(Icons.settings_outlined), label: Text('Paramètres')),
          ],
          unselectedIconTheme: const IconThemeData(color: Color(0xFFB8C5DC)),
          selectedIconTheme: const IconThemeData(color: Colors.white),
          unselectedLabelTextStyle: const TextStyle(color: Color(0xFFB8C5DC)),
          selectedLabelTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        Expanded(child: ColoredBox(
          color: AppTheme.canvas,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(
              height: 76,
              padding: const EdgeInsets.symmetric(horizontal: 30),
              decoration: const BoxDecoration(color: Colors.white, border: Border(bottom: BorderSide(color: AppTheme.border))),
              child: const Row(children: [
                Text('Espace de gestion', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                Spacer(),
                Icon(Icons.cloud_off_outlined, color: AppTheme.muted, size: 18),
                SizedBox(width: 8),
                Text('Mode hors connexion', style: TextStyle(color: AppTheme.muted)),
              ]),
            ),
            Expanded(child: FutureBuilder<List<int>>(
              future: Future.wait([
                db.select(db.schoolYears).get().then((v) => v.length),
                db.select(db.classes).get().then((v) => v.length),
                db.select(db.students).get().then((v) => v.length),
                db.select(db.subjects).get().then((v) => v.length),
              ]),
              builder: (context, snapshot) {
                final values = snapshot.data ?? [0, 0, 0, 0];
                const labels = ['Années scolaires', 'Classes', 'Élèves', 'Matières'];
                const icons = [Icons.calendar_month, Icons.meeting_room, Icons.groups, Icons.menu_book];
                return ListView(padding: const EdgeInsets.all(30), children: [
                  const Text('Tableau de bord', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: AppTheme.ink)),
                  const SizedBox(height: 8),
                  const Text('Vue générale de votre établissement scolaire.', style: TextStyle(color: AppTheme.muted)),
                  const SizedBox(height: 26),
                  LayoutBuilder(builder: (context, box) {
                    final columns = box.maxWidth > 950 ? 4 : box.maxWidth > 580 ? 2 : 1;
                    return GridView.count(
                      crossAxisCount: columns, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 14, mainAxisSpacing: 14, childAspectRatio: 2.2,
                      children: List.generate(4, (i) => _StatCard(label: labels[i], value: values[i], icon: icons[i])),
                    );
                  }),
                  const SizedBox(height: 22),
                  Card(child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Bienvenue dans GESCO', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      const Text('Le socle local est initialisé. Les prochains modules ajouteront les paramètres, les élèves, les notes et les bulletins.'),
                      const SizedBox(height: 16),
                      const Wrap(spacing: 10, children: [
                        Chip(avatar: Icon(Icons.storage, size: 17), label: Text('SQLite local')),
                        Chip(avatar: Icon(Icons.cloud_off, size: 17), label: Text('Sans serveur')),
                        Chip(avatar: Icon(Icons.desktop_windows, size: 17), label: Text('Windows en priorité')),
                      ]),
                    ]),
                  )),
                ]);
              },
            )),
          ]),
        )),
      ]),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.icon});
  final String label;
  final int value;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.all(18),
    child: Row(children: [
      Container(width: 44, height: 44, decoration: BoxDecoration(color: AppTheme.blue.withValues(alpha: .10), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: AppTheme.blue)),
      const SizedBox(width: 13),
      Expanded(child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: AppTheme.muted, fontSize: 12, fontWeight: FontWeight.w600)),
        const SizedBox(height: 5),
        Text('$value', style: const TextStyle(fontSize: 25, fontWeight: FontWeight.w800, color: AppTheme.ink)),
      ])),
    ]),
  ));
}
