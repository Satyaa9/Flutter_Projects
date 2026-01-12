import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_application_1/Profile.dart';

class LoginPage extends StatelessWidget {
  LoginPage({super.key});
  TextEditingController emailController = TextEditingController();
  TextEditingController passwordController = TextEditingController();

  Future<void> login(
    String email,
    String password,
    BuildContext context,
  ) async {
    await FirebaseAuth.instance.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => Profile(email: email)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Login Page")),
      body: Center(
        child: Column(
          children: [
            TextField(controller: emailController),
            TextField(controller: passwordController),
            ElevatedButton(
              onPressed: () {
                login(emailController.text, passwordController.text, context);
              },
              child: Text("Register"),
            ),
          ],
        ),
      ),
    );
  }
}
