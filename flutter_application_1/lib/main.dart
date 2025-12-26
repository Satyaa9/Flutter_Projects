import 'package:flutter/material.dart';

void main() {
  runApp(const Demo());
}

// class Demo extends StatelessWidget {
//   const Demo({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       home: Scaffold(
//         //Simple 1 box centre madhe gheun kahitari text lihili aahe.

//         // body: Center(
//         //   child: Container(
//         //     height: 100,
//         //     width: 100,
//         //     color: Colors.red,
//         //     child: Center(child: Text("Satish")),
//         //   ),
//         // ),
//         // body: Column(
//         //   children: [
//         //     Container(
//         //       height: 100,
//         //       width: 100,
//         //       color: Colors.red,
//         //       child: Text("Satish"),
//         //       // margin: EdgeInsets.only(top: 30),
//         //       // margin: EdgeInsets.all(100),
//         //     ),
//         //     Container(
//         //       height: 100,
//         //       width: 100,
//         //       color: Colors.green,
//         //       child: Text("Snehal"),
//         //     ),
//         //   ],
//         // ),
//         // body: Row(
//         //   children: [
//         //     Container(height: 100, width: 100, color: Colors.red),
//         //     Container(height: 100, width: 100, color: Colors.green),
//         //   ],
//         // ),

//         //navbar

//       ),
//     );
//   }
// }

class Demo extends StatelessWidget {
  const Demo({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter navbar',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: Homepage(),
    );
  }
}

class Homepage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Navbar'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              print('search clicked');
            },
          ),
          IconButton(
            onPressed: () {
              print('Notification clicked');
            },
            icon: const Icon(Icons.notifications),
          ),
        ],
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const SecondPage()),
            );
          },
          child: const Text('Go to second page'),
        ),
      ),
    );
  }
}

class SecondPage extends StatelessWidget {
  const SecondPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Second page')),
      body: Center(child: Text('Wlcome to second page')),
    );
  }
}
