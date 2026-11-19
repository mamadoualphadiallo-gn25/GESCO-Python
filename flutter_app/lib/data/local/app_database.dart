import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

part 'app_database.g.dart';

class SchoolYears extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get label => text().unique()();
  DateTimeColumn get startsAt => dateTime()();
  DateTimeColumn get endsAt => dateTime()();
  BoolColumn get isCurrent => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}

class Classes extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text()();
  TextColumn get level => text().nullable()();
  IntColumn get schoolYearId => integer().references(SchoolYears, #id)();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
  @override
  List<Set<Column>> get uniqueKeys => [{name, schoolYearId}];
}

class Students extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get matricule => text().unique()();
  TextColumn get lastName => text()();
  TextColumn get firstName => text()();
  TextColumn get sex => text().nullable()();
  DateTimeColumn get birthDate => dateTime().nullable()();
  TextColumn get birthPlace => text().nullable()();
  TextColumn get fatherName => text().nullable()();
  TextColumn get motherName => text().nullable()();
  TextColumn get guardianContact => text().nullable()();
  TextColumn get address => text().nullable()();
  TextColumn get photoPath => text().nullable()();
  BoolColumn get isArchived => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}

class Enrollments extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get studentId => integer().references(Students, #id)();
  IntColumn get classId => integer().references(Classes, #id)();
  IntColumn get schoolYearId => integer().references(SchoolYears, #id)();
  DateTimeColumn get enrolledAt => dateTime().withDefault(currentDateAndTime)();
  @override
  List<Set<Column>> get uniqueKeys => [{studentId, schoolYearId}];
}

class Subjects extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text().unique()();
  TextColumn get shortName => text().nullable()();
}

class ClassSubjects extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get classId => integer().references(Classes, #id)();
  IntColumn get subjectId => integer().references(Subjects, #id)();
  RealColumn get coefficient => real().withDefault(const Constant(1))();
  @override
  List<Set<Column>> get uniqueKeys => [{classId, subjectId}];
}

class Periods extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get schoolYearId => integer().references(SchoolYears, #id)();
  TextColumn get code => text()();
  TextColumn get label => text()();
  TextColumn get kind => text()();
  IntColumn get sequence => integer()();
  @override
  List<Set<Column>> get uniqueKeys => [{schoolYearId, code}];
}

class Grades extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get studentId => integer().references(Students, #id)();
  IntColumn get subjectId => integer().references(Subjects, #id)();
  IntColumn get periodId => integer().references(Periods, #id)();
  TextColumn get assessmentType => text()();
  RealColumn get score => real().nullable()();
  RealColumn get maxScore => real().withDefault(const Constant(20))();
  RealColumn get coefficientSnapshot => real().withDefault(const Constant(1))();
  TextColumn get comment => text().nullable()();
  DateTimeColumn get updatedAt => dateTime().withDefault(currentDateAndTime)();
}

@DriftDatabase(tables: [SchoolYears, Classes, Students, Enrollments, Subjects, ClassSubjects, Periods, Grades])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(driftDatabase(name: 'gesco_local'));
  @override
  int get schemaVersion => 1;
}

final databaseProvider = Provider<AppDatabase>((ref) {
  throw StateError('AppDatabase doit être fourni au démarrage de GESCO.');
});
