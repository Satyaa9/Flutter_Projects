import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_application_1/LoginPage.dart';
import 'package:flutter_application_1/Profile.dart';

class Homepage extends StatelessWidget {
  Homepage({super.key});
  TextEditingController emailController = TextEditingController();
  TextEditingController passwordController = TextEditingController();

  Future<void> register(
    String email,
    String password,
    BuildContext context,
  ) async {
    var user = await FirebaseAuth.instance.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );
    emailController.clear();
    passwordController.clear();
    print("user register");

    await FirebaseFirestore.instance
        .collection("users")
        .doc(user.user!.uid)
        .set({"email": email, "createdAt": Timestamp.now()});

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => Profile(email: email)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Auth")),
      body: Center(
        child: Column(
          children: [
            TextField(controller: emailController),
            TextField(controller: passwordController),
            ElevatedButton(
              onPressed: () {
                register(
                  emailController.text,
                  passwordController.text,
                  context,
                );
              },
              child: Text("Register"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => LoginPage()),
                );
              },
              child: Text("got to Login page"),
            ),
          ],
        ),
      ),
    );
  }
}
