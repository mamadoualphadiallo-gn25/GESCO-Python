import 'package:flutter_test/flutter_test.dart';
import 'package:gesco/domain/calculations/weighted_average.dart';

void main() {
  group('weightedAverage', () {
    test('calculates weighted average', () {
      expect(weightedAverage([
        const GradeEntry(score: 12, coefficient: 2),
        const GradeEntry(score: 16, coefficient: 1),
      ]), closeTo(13.333333, 0.00001));
    });
    test('does not convert a missing grade to zero', () {
      expect(weightedAverage([
        const GradeEntry(score: 14, coefficient: 2),
        const GradeEntry(score: null, coefficient: 5),
      ]), 14);
    });
    test('returns null when all grades are missing', () {
      expect(weightedAverage([const GradeEntry(score: null, coefficient: 1)]), isNull);
    });
    test('rejects invalid coefficients', () {
      expect(() => weightedAverage([
        const GradeEntry(score: 10, coefficient: 0),
      ]), throwsArgumentError);
    });
  });
}
