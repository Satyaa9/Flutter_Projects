import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_application_1/Authentication.dart';
import 'package:flutter_application_1/Homepage.dart';
import 'package:flutter_application_1/firebase_options.dart';

void main() async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  print('Initialized default app ');
  runApp(const Demo());
}

class Demo extends StatelessWidget {
  const Demo({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter navbar',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: Authentication(),
    );
  }
}
