# 🎮 Splunk Arcade Questions Editor

This is a **Node.js web application** that allows you to **edit JSON-based quiz questions** for Splunk Arcade. The app provides a simple **web-based UI** for editing questions, deleting questions, and ensuring validation before saving.

---

## 🚀 Features

- **Load and Edit Questions** from a JSON file.
- **Validate** that each question has exactly **one correct answer**.
- **Delete Questions** dynamically with automatic reordering.
- **Save to a New JSON File (`*-new.json`)** to prevent overwriting the original.
- **Web-Based UI** with an intuitive editor.

---

## 🛠 Installation

### **1️⃣ Prerequisites**

- [Node.js](https://nodejs.org/) **(v16 or later)**
- npm (comes with Node.js)

### **2 Install Dependencies:

```sh
   npm install
```

---

## Running the application

### **1️⃣ Start the server

```sh
   node server.js
```

OR specify a custom JSON file:

```sh
   node server.js -f ../../player-content/questions.json
```

### **2️⃣ Access the UI**

- Open a browser and go to: 

   http://localhost:3000

---

## 📂 File Structure

📦 questions-edit
 ├── public/          # Frontend UI (auto-generated)
 ├── server.js        # Main Node.js server
 ├── package.json     # Dependencies and scripts
 ├── README.md        # Documentation

---

## 📌 How to Use

1. **Open the Editor** at `http://localhost:3000`
2. **Edit Questions** in the text fields.
3. **Delete Questions** using the ❌ button.
4. **Ensure One Correct Answer** is checked per question.
5. **Click Save** to store changes in `*-new.json`.

---

## 📜 Example Question Format

```json
{
  "General Knowledge": [
    {
      "question": "You'll have a dashboard with some data to investigate...",
      "choices": [
        { "prompt": "It tracks player engagement", "is_correct": true },
        { "prompt": "It measures server health", "is_correct": false }
      ]
    }
  ]
}
```

---

## ⚠️ Validation Rules
- **Every question must have one and only one correct answer.**
- **Missing or multiple correct answers prevent saving.**

---

## 🔧 Troubleshooting

### **Port Already in Use**

If `3000` is in use, run:

```sh
PORT=5000 node server.js
```

Then visit http://localhost:5000

### **File Not Found Error**

Ensure your JSON file exists at the specified path.

---

## 📜 License
MIT License © 2024 Pieter Hagen / Splunk Arcade Team

---

🚀 **Enjoy Editing Your Splunk Arcade Questions!** 🚀