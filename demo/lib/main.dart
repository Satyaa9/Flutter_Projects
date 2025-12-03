import 'package:demo/homescreen.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // You only need to return one MaterialApp widget
    return MaterialApp(
      home: Homescreen(), // Assuming Homescreen is defined in homescreen.dart
    );
  }
}
