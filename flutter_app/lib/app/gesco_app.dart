import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/local/app_database.dart';
import '../features/management/management_page.dart';
import '../features/grades/grades_page.dart';
import '../features/results/rankings_page.dart';
import '../features/printing/teacher_sheet_page.dart';
import '../features/printing/bulletins_page.dart';
import 'theme/app_theme.dart';

class GescoApp extends StatelessWidget {
  const GescoApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'GESCO', debugShowCheckedModeBanner: false,
    theme: AppTheme.light, home: const DashboardScreen(),
  );
}

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});
  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  int selected = 0;
  static const labels = ['Tableau de bord', 'Élèves', 'Classes', 'Matières', 'Notes', 'Classements', 'Fiches professeurs', 'Années scolaires', 'Bulletins'];
  static const icons = [Icons.dashboard_outlined, Icons.people_outline, Icons.meeting_room_outlined, Icons.menu_book_outlined, Icons.edit_note_outlined, Icons.leaderboard_outlined, Icons.description_outlined, Icons.calendar_month_outlined, Icons.picture_as_pdf_outlined];

  @override
  Widget build(BuildContext context) {
    final db = ref.watch(databaseProvider);
    Widget page;
    if (selected == 1) {
      page = ManagementPage(database: db, section: GescoSection.students);
    } else if (selected == 2) {
      page = ManagementPage(database: db, section: GescoSection.classes);
    } else if (selected == 3) {
      page = ManagementPage(database: db, section: GescoSection.subjects);
    } else if (selected == 7) {
      page = ManagementPage(database: db, section: GescoSection.years);
    } else if (selected == 4) {
      page = GradesPage(database: db);
    } else if (selected == 5) {
      page = RankingsPage(database: db);
    } else if (selected == 6) {
      page = TeacherSheetPage(database: db);
    } else if (selected == 8) {
      page = BulletinsPage(database: db);
    } else if (selected == 0) {
      page = _DashboardContent(database: db);
    } else {
      page = _ComingSoonPage(title: labels[selected]);
    }
    return Scaffold(
      body: Row(children: [
        NavigationRail(
          extended: MediaQuery.sizeOf(context).width > 1050,
          backgroundColor: AppTheme.navy,
          selectedIndex: selected,
          onDestinationSelected: (value) => setState(() => selected = value),
          leading: const Padding(
            padding: EdgeInsets.symmetric(vertical: 26),
            child: Column(children: [
              Icon(Icons.school_rounded, color: Colors.white, size: 34),
              SizedBox(height: 8),
              Text('GESCO', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
            ]),
          ),
          destinations: List.generate(labels.length, (i) => NavigationRailDestination(icon: Icon(icons[i]), label: Text(labels[i]))),
          unselectedIconTheme: const IconThemeData(color: Color(0xFFB8C5DC)),
          selectedIconTheme: const IconThemeData(color: Colors.white),
          unselectedLabelTextStyle: const TextStyle(color: Color(0xFFB8C5DC)),
          selectedLabelTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        Expanded(child: ColoredBox(color: AppTheme.canvas, child: Column(children: [
          Container(height: 76, padding: const EdgeInsets.symmetric(horizontal: 30),
            decoration: const BoxDecoration(color: Colors.white, border: Border(bottom: BorderSide(color: AppTheme.border))),
            child: Row(children: [
              Text(labels[selected], style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              const Spacer(),
              const Icon(Icons.cloud_off_outlined, color: AppTheme.muted, size: 18),
              const SizedBox(width: 8),
              const Text('Mode hors connexion', style: TextStyle(color: AppTheme.muted)),
            ]),
          ),
          Expanded(child: page),
        ]))),
      ]),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent({required this.database});
  final AppDatabase database;
  @override
  Widget build(BuildContext context) => FutureBuilder<List<int>>(
    future: Future.wait([
      database.select(database.schoolYears).get().then((v) => v.length),
      database.select(database.classes).get().then((v) => v.length),
      database.select(database.students).get().then((v) => v.length),
      database.select(database.subjects).get().then((v) => v.length),
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
          return GridView.count(crossAxisCount: columns, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), crossAxisSpacing: 14, mainAxisSpacing: 14, childAspectRatio: 2.2,
            children: List.generate(4, (i) => _StatCard(label: labels[i], value: values[i], icon: icons[i])));
        }),
        const SizedBox(height: 22),
        const Card(child: Padding(padding: EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Bienvenue dans GESCO', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
          SizedBox(height: 8),
          Text('GESCO fonctionne avec une base SQLite locale. Les données restent sur cet appareil et aucune connexion Internet n’est nécessaire.'),
          SizedBox(height: 16),
          Wrap(spacing: 10, children: [
            Chip(avatar: Icon(Icons.storage, size: 17), label: Text('SQLite local')),
            Chip(avatar: Icon(Icons.cloud_off, size: 17), label: Text('Sans serveur')),
            Chip(avatar: Icon(Icons.desktop_windows, size: 17), label: Text('Windows en priorité')),
          ]),
        ]))),
      ]);
    },
  );
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.icon});
  final String label; final int value; final IconData icon;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Row(children: [
    Container(width: 44, height: 44, decoration: BoxDecoration(color: AppTheme.blue.withValues(alpha: .10), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: AppTheme.blue)),
    const SizedBox(width: 13),
    Expanded(child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: AppTheme.muted, fontSize: 12, fontWeight: FontWeight.w600)),
      const SizedBox(height: 5), Text('$value', style: const TextStyle(fontSize: 25, fontWeight: FontWeight.w800, color: AppTheme.ink)),
    ])),
  ])));
}

class _ComingSoonPage extends StatelessWidget {
  const _ComingSoonPage({required this.title});
  final String title;
  @override
  Widget build(BuildContext context) => Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
    const Icon(Icons.construction_outlined, size: 48, color: AppTheme.muted),
    const SizedBox(height: 14), Text(title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
    const SizedBox(height: 8), const Text('Module prévu dans les prochaines étapes du développement.', style: TextStyle(color: AppTheme.muted)),
  ]));
}
