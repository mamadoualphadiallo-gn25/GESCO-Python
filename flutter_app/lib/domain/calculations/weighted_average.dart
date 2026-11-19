class GradeEntry {
  const GradeEntry({required this.score, required this.coefficient});
  final double? score;
  final double coefficient;
}

double? weightedAverage(Iterable<GradeEntry> entries) {
  var weightedTotal = 0.0;
  var coefficientTotal = 0.0;
  for (final entry in entries) {
    final score = entry.score;
    if (score == null) continue;
    if (!score.isFinite || !entry.coefficient.isFinite || entry.coefficient <= 0 || score < 0) {
      throw ArgumentError('Note ou coefficient invalide.');
    }
    weightedTotal += score * entry.coefficient;
    coefficientTotal += entry.coefficient;
  }
  if (coefficientTotal == 0) return null;
  return weightedTotal / coefficientTotal;
}
