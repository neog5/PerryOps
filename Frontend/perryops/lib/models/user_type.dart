enum UserType { staff, patient }

extension UserTypeX on UserType {
  String get label => switch (this) {
    UserType.staff => 'Staff',
    UserType.patient => 'Patient',
  };
}
