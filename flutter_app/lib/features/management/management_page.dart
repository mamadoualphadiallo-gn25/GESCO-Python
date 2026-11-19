import 'package:flutter/material.dart';
import '../../data/local/app_database.dart';
import '../../app/theme/app_theme.dart';

enum GescoSection { years, classes, subjects, students }

class ManagementPage extends StatefulWidget {
  const ManagementPage({super.key, required this.database, required this.section});
  final AppDatabase database;
  final GescoSection section;

  @override
  State<ManagementPage> createState() => _ManagementPageState();
}

class _ManagementPageState extends State<ManagementPage> {
  bool loading = true;
  List<Map<String, Object?>> rows = [];
  late final _Definition definition;

  @override
  void initState() {
    super.initState();
    definition = _definitions[widget.section]!;
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    final result = await widget.database.customSelect(definition.query).get();
    if (!mounted) return;
    setState(() {
      rows = result.map((row) => Map<String, Object?>.from(row.data)).toList();
      loading = false;
    });
  }

  Future<void> _edit([Map<String, Object?>? row]) async {
    final controllers = <String, TextEditingController>{
      for (final field in definition.fields)
        field.key: TextEditingController(text: row?[field.key]?.toString() ?? ''),
    };
    final formKey = GlobalKey<FormState>();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(row == null ? 'Ajouter : ${definition.title}' : 'Modifier : ${definition.title}'),
        content: SizedBox(
          width: 480,
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (final field in definition.fields)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: TextFormField(
                        controller: controllers[field.key],
                        decoration: InputDecoration(labelText: field.label, hintText: field.hint),
                        keyboardType: field.numeric ? TextInputType.number : TextInputType.text,
                        validator: (value) => field.required && (value == null || value.trim().isEmpty) ? 'Champ obligatoire' : null,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Annuler')),
          FilledButton(onPressed: () {
            if (formKey.currentState!.validate()) Navigator.pop(dialogContext, true);
          }, child: const Text('Enregistrer')),
        ],
      ),
    );
    if (accepted == true) {
      final values = {for (final field in definition.fields) field.key: controllers[field.key]!.text.trim()};
      final columns = values.keys.toList();
      final placeholders = List.filled(columns.length, '?').join(', ');
      final args = columns.map((key) {
        final value = values[key]!;
        if (value.isEmpty) return null;
        if (definition.dateKeys.contains(key)) return DateTime.parse(value).millisecondsSinceEpoch;
        if (definition.numericKeys.contains(key)) return int.tryParse(value) ?? double.tryParse(value);
        return value;
      }).toList();
      if (row == null) {
        await widget.database.customStatement(
          'INSERT INTO ${definition.table} (${columns.join(', ')}) VALUES ($placeholders)', args);
      } else {
        final assignments = columns.map((key) => '$key = ?').join(', ');
        await widget.database.customStatement(
          'UPDATE ${definition.table} SET $assignments WHERE id = ?', [...args, row['id']]);
      }
      await _load();
    }
    for (final controller in controllers.values) {
      controller.dispose();
    }
  }

  Future<void> _delete(Map<String, Object?> row) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmer la suppression'),
        content: const Text('Cette opération peut être refusée si cet élément est déjà utilisé dans des données scolaires.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Supprimer')),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await widget.database.customStatement('DELETE FROM ${definition.table} WHERE id = ?', [row['id']]);
        await _load();
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Suppression impossible : cet élément est utilisé ailleurs.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(28),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(definition.title, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppTheme.ink)),
          const SizedBox(height: 5),
          Text(definition.subtitle, style: const TextStyle(color: AppTheme.muted)),
        ])),
        FilledButton.icon(onPressed: () => _edit(), icon: const Icon(Icons.add), label: Text('Ajouter')),
      ]),
      const SizedBox(height: 20),
      Expanded(child: Card(child: loading
        ? const Center(child: CircularProgressIndicator())
        : rows.isEmpty
          ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.inbox_outlined, size: 44, color: AppTheme.muted),
              const SizedBox(height: 12),
              Text('Aucun élément enregistré dans ${definition.title.toLowerCase()}.'),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: () => _edit(), icon: const Icon(Icons.add), label: const Text('Créer le premier')),
            ]))
          : ListView.separated(
              itemCount: rows.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final row = rows[index];
                return ListTile(
                  leading: CircleAvatar(backgroundColor: AppTheme.blue.withValues(alpha: .10), child: Icon(definition.icon, color: AppTheme.blue)),
                  title: Text(definition.display(row), style: const TextStyle(fontWeight: FontWeight.w700)),
                  subtitle: Text(definition.fields.map((f) => '${f.label} : ${row[f.key] ?? '—'}').join('  •  ')),
                  trailing: Wrap(children: [
                    IconButton(tooltip: 'Modifier', onPressed: () => _edit(row), icon: const Icon(Icons.edit_outlined)),
                    IconButton(tooltip: 'Supprimer', onPressed: () => _delete(row), icon: const Icon(Icons.delete_outline, color: Colors.redAccent)),
                  ]),
                );
              },
            ))),
    ]),
  );
}

class _Field {
  const _Field(this.key, this.label, {this.hint, this.required = false, this.numeric = false});
  final String key, label;
  final String? hint;
  final bool required, numeric;
}

class _Definition {
  const _Definition({required this.title, required this.subtitle, required this.table, required this.query, required this.fields, required this.icon, required this.display, this.numericKeys = const {}, this.dateKeys = const {}});
  final String title, subtitle, table, query;
  final List<_Field> fields;
  final IconData icon;
  final String Function(Map<String, Object?>) display;
  final Set<String> numericKeys;
  final Set<String> dateKeys;
}

const _definitions = <GescoSection, _Definition>{
  GescoSection.years: _Definition(
    title: 'Années scolaires', subtitle: 'Créer et conserver les années scolaires.', table: 'school_years',
    query: 'SELECT id, label, starts_at, ends_at, is_current FROM school_years ORDER BY starts_at DESC',
    fields: [_Field('label', 'Libellé', required: true, hint: '2026-2027'), _Field('starts_at', 'Date de début', required: true, hint: '2026-10-01'), _Field('ends_at', 'Date de fin', required: true, hint: '2027-06-30'), _Field('is_current', 'Année courante (0 ou 1)', numeric: true)],
    icon: Icons.calendar_month, display: (r) => '${r['label']}',
  ),
  GescoSection.classes: _Definition(
    title: 'Classes', subtitle: 'Organiser les classes par année scolaire.', table: 'classes',
    query: 'SELECT id, name, level, school_year_id FROM classes ORDER BY name',
    fields: [_Field('name', 'Nom de la classe', required: true), _Field('level', 'Niveau'), _Field('school_year_id', 'Identifiant de l’année scolaire', required: true, numeric: true)],
    icon: Icons.meeting_room_outlined, display: (r) => '${r['name']}',
    numericKeys: {'school_year_id'},
  ),
  GescoSection.subjects: _Definition(
    title: 'Matières', subtitle: 'Créer le catalogue des matières.', table: 'subjects',
    query: 'SELECT id, name, short_name FROM subjects ORDER BY name',
    fields: [_Field('name', 'Nom de la matière', required: true), _Field('short_name', 'Abréviation')],
    icon: Icons.menu_book_outlined, display: (r) => '${r['name']}',
  ),
  GescoSection.students: _Definition(
    title: 'Élèves', subtitle: 'Créer et gérer les fiches des élèves.', table: 'students',
    query: 'SELECT id, matricule, last_name, first_name, sex, guardian_contact FROM students WHERE is_archived = 0 ORDER BY last_name, first_name',
    fields: [_Field('matricule', 'Matricule', required: true), _Field('last_name', 'Nom', required: true), _Field('first_name', 'Prénom', required: true), _Field('sex', 'Sexe'), _Field('guardian_contact', 'Contact du parent')],
    icon: Icons.person_outline, display: (r) => '${r['last_name']} ${r['first_name']}',
  ),
};
