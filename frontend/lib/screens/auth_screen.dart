import 'package:flutter/material.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  
  bool _isLoginMode = true;  // true = sign in, false = registry
  bool _isLoading = false;    // loading bar
  String _errorMessage = '';
  
  Future<void> _handleAuth() async {
    setState(() {
      _errorMessage = '';
      _isLoading = true;
    });
    
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    
    if (username.isEmpty || password.isEmpty) {
      setState(() {
        _errorMessage = 'Заполните все поля';
        _isLoading = false;
      });
      return;
    }
    
    if (!username.startsWith('@')) {
      setState(() {
        _errorMessage = 'Имя пользователя должно начинаться с @';
        _isLoading = false;
      });
      return;
    }
    
    try {
      // TODO: Здесь будет подключение к серверу
      // Пока просто имитируем задержку
      await Future.delayed(const Duration(seconds: 1));
      
      // Если всё успешно - переходим в чат
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/chat');
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Ошибка подключения: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.chat_bubble_outline,
                size: 80,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 16),
              Text(
                'SIGPIPE Chat',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 48),
              
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment<bool>(value: true, label: Text('Вход')),
                  ButtonSegment<bool>(value: false, label: Text('Регистрация')),
                ],
                selected: {_isLoginMode},
                onSelectionChanged: (Set<bool> newSelection) {
                  setState(() {
                    _isLoginMode = newSelection.first;
                    _errorMessage = '';
                  });
                },
              ),
              const SizedBox(height: 32),
              
              // Username input
              TextField(
                controller: _usernameController,
                decoration: const InputDecoration(
                  labelText: 'Имя пользователя',
                  hintText: '@username',
                  prefixIcon: Icon(Icons.person),
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
              ),
              const SizedBox(height: 16),
              
              // Password input
              TextField(
                controller: _passwordController,
                decoration: const InputDecoration(
                  labelText: 'Пароль',
                  prefixIcon: Icon(Icons.lock),
                  border: OutlineInputBorder(),
                ),
                obscureText: true,  // скрываем ввод
              ),
              const SizedBox(height: 16),
              
              if (_errorMessage.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(
                    _errorMessage,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              
              // Button
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleAuth,
                  child: _isLoading
                      ? const CircularProgressIndicator()
                      : Text(_isLoginMode ? 'Войти' : 'Зарегистрироваться'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
