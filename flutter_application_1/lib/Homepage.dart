import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

class Homepage extends StatefulWidget {
  Homepage({super.key});

  @override
  State<Homepage> createState() => _HomepageState();
}

class _HomepageState extends State<Homepage> {
  var firestore = FirebaseFirestore.instance.collection("gulams");
  late Future<QuerySnapshot> employeeData;
  Future<QuerySnapshot> get() async {
    return firestore.get();
  }

  @override
  void initState() {
    super.initState();
    employeeData = get();
  }

  Future<void> deleteEmployee(String id) async {
    await firestore.doc(id).delete();
    setState(() {
      employeeData = get();
    });
  }

  Future<void> updateEmployee(String id) async {
    await firestore.doc(id).update({"name": "kartik", "company": "Ature"});
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    print("in build");
    return Scaffold(
      appBar: AppBar(title: Text("firestore demo")),
      body: StreamBuilder<QuerySnapshot>(
        stream: firestore.snapshots(),
        builder: (context, snapshot) {
          print(snapshot);
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            print("hello jatay ka ithparent");
            return Text("No data Found");
          }
          final employess = snapshot.data!.docs;
          return ListView.builder(
            itemCount: employess.length,
            itemBuilder: (context, index) {
              final employee = employess[index];
              return ListTile(
                title: Text(employee["name"]),
                subtitle: Text(employee["company"]),
                trailing: IconButton(
                  onPressed: () => deleteEmployee(employee.id),
                  icon: Icon(Icons.remove),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
