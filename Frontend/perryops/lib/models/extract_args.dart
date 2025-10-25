class ExtractArgs {
  final String sessionId;
  final String patientId;
  final String? patientName;

  const ExtractArgs({
    required this.sessionId,
    required this.patientId,
    this.patientName,
  });
}
