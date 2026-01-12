import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class Profile extends StatelessWidget {
  final String? email;
  const Profile({super.key, this.email});

  @override
  Widget build(BuildContext context) {
    print("build : $email");
    return Scaffold(
      appBar: AppBar(title: Text("$email")),
      body: Center(
        child: ElevatedButton(
          onPressed: () async {
            await FirebaseAuth.instance.signOut();
          },
          child: Text("logout"),
        ),
      ),
    );
  }
}
