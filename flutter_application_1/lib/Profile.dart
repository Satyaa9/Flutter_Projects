import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class Profile extends StatelessWidget {
  final String? email;
  Profile({super.key, this.email});
  TextEditingController taskController = TextEditingController();
  var user = FirebaseAuth.instance.currentUser!;
  Future<void> addTask() async {
    await FirebaseFirestore.instance.collection("tasks").add({
      "taskname": taskController.text,
      "userId": user.uid,
    });
    taskController.clear();
  }

  @override
  Widget build(BuildContext context) {
    print("build : $email");
    return Scaffold(
      appBar: AppBar(title: Text("$email")),
      body: Column(
        children: [
          TextField(controller: taskController),
          ElevatedButton(onPressed: addTask, child: Text("Add")),
          Expanded(
            child: StreamBuilder(
              stream: FirebaseFirestore.instance
                  .collection("tasks")
                  .where("userId", isEqualTo: user.uid)
                  .snapshots(),
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return Center(child: CircularProgressIndicator());
                }
                var tasks = snapshot.data!.docs;
                return ListView.builder(
                  itemCount: tasks.length,
                  itemBuilder: (context, index) {
                    return ListTile(title: Text(tasks[index]["taskname"]));
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await FirebaseAuth.instance.signOut();
        },
        child: Text("logout"),
      ),
    );
  }
}
