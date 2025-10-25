import 'user_type.dart';

class HomeArgs {
  final UserType userType;
  final String? name;
  final String? userId;

  const HomeArgs({required this.userType, this.name, this.userId});
}
