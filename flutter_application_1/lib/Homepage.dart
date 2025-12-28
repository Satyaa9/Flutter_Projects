import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

class Homepage extends StatelessWidget {
  Homepage({super.key});

  Future<List<QueryDocumentSnapshot>> get() async {
    var firestore = FirebaseFirestore.instance.collection("gulams");
    QuerySnapshot snapshot = await firestore.get();
    return snapshot.docs;
  }

  @override
  Widget build(BuildContext context) {
    print("in build");
    return Scaffold(
      appBar: AppBar(title: Text("firestore demo")),
      body: FutureBuilder(
        future: get(),
        builder: (context, snapshot) {
          print(snapshot);
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            print("hello jatay ka ithparent");
            return Text("No data Found");
          }
          final employess = snapshot.data!;
          return ListView.builder(
            itemCount: employess.length,
            itemBuilder: (context, index) {
              final employee = employess[index];
              return ListTile(
                title: Text(employee["name"]),
                subtitle: Text(employee["company"]),
              );
            },
          );
        },
      ),
    );
  }
}
