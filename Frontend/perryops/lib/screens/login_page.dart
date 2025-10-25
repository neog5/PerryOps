import 'package:flutter/material.dart';
import '../widgets/ui.dart';
import '../models/user_type.dart';
import '../utils/validators.dart';
import '../services/auth_service.dart';
import '../models/auth_response.dart';
import '../models/home_args.dart';
import '../services/notification_service.dart';
import '../services/device_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  UserType? _selectedType;
  bool _isSubmitting = false;
  bool _obscure = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final valid = _formKey.currentState?.validate() ?? false;
    if (!valid || _selectedType == null) {
      if (_selectedType == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select user type')),
        );
      }
      return;
    }
    setState(() => _isSubmitting = true);
    try {
      final auth = const AuthService();
      AuthResponse resp;
      if (_selectedType == UserType.staff) {
        resp = await auth.loginCpc(_emailCtrl.text.trim(), _passwordCtrl.text);
      } else {
        resp = await auth.loginPatient(
          _emailCtrl.text.trim(),
          _passwordCtrl.text,
        );
      }
      if (!mounted) return;
      // If patient, generate/register device token (non-blocking UX)
      if (_selectedType == UserType.patient) {
        try {
          final token =
              await const NotificationService().getOrCreateDeviceToken();
          if (token.isNotEmpty) {
            await const DeviceService().registerDeviceToken(resp.userId, token);
          }
        } catch (e) {
          // Don't block navigation on failure; surface a lightweight notice
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Could not register device for notifications'),
              ),
            );
          }
        }
      }

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Welcome ${resp.name}')));
      Navigator.pushReplacementNamed(
        context,
        '/home',
        arguments: HomeArgs(
          userType: _selectedType!,
          name: resp.name,
          userId: resp.userId,
        ),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(e.message)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Login failed')));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: SingleChildScrollView(
        child: PageContainer(
          maxWidth: 520,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.login,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Sign in',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const SectionHeader(
                      'Choose user type',
                      icon: Icons.account_circle,
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<UserType>(
                      value: _selectedType,
                      items: const [
                        DropdownMenuItem(
                          value: UserType.staff,
                          child: Text('Staff'),
                        ),
                        DropdownMenuItem(
                          value: UserType.patient,
                          child: Text('Patient'),
                        ),
                      ],
                      onChanged: (v) => setState(() => _selectedType = v),
                      decoration: const InputDecoration(
                        labelText: 'User type',
                        prefixIcon: Icon(Icons.account_circle),
                      ),
                    ),
                    const Divider(height: 32),
                    TextFormField(
                      controller: _emailCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        hintText: 'name@example.com',
                        prefixIcon: Icon(Icons.email),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      validator: Validators.email,
                      autofillHints: const [
                        AutofillHints.username,
                        AutofillHints.email,
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _passwordCtrl,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscure ? Icons.visibility : Icons.visibility_off,
                          ),
                          onPressed: () => setState(() => _obscure = !_obscure),
                        ),
                      ),
                      obscureText: _obscure,
                      validator: Validators.password,
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: _isSubmitting ? null : _submit,
                      child:
                          _isSubmitting
                              ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                              : const Text('Login'),
                    ),
                    // Removed disabled signup note as requested
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
