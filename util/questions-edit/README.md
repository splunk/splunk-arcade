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
   npm install

---
## RUNNING THE APPLICATION:

1) Start the server:
   node server.js

   OR specify a custom JSON file:
   node server.js -f ../../player-content/questions.json

2) Access the UI:
   Open a web browser and go to:
   http://localhost:3000

--------------------------------------------------------------------

📦 splunk-arcade-editor
 ├── public/          # Frontend UI (auto-generated)
 ├── server.js        # Main Node.js server
 ├── package.json     # Dependencies and scripts
 ├── README.md        # Documentation

--------------------------------------------------------------------

HOW TO USE:

1) Open the editor in your browser: http://localhost:3000
2) Edit questions using the text fields.
3) Delete questions using the "Delete" button.
4) Ensure that one and only one correct answer is checked per question.
5) Click "Save" to store changes in a new JSON file (*-new.json).

--------------------------------------------------------------------

EXAMPLE QUESTION FORMAT:

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

--------------------------------------------------------------------

VALIDATION RULES:
- Every question must have one and only one correct answer.
- Missing or multiple correct answers will prevent saving.

--------------------------------------------------------------------

TROUBLESHOOTING:

PORT ALREADY IN USE:
- If port 3000 is already in use, try running:
  PORT=5000 node server.js
  Then visit http://localhost:5000

FILE NOT FOUND ERROR:
- Ensure that your JSON file exists at the specified path.

--------------------------------------------------------------------

LICENSE:
MIT License © 2024 Pieter Hagen / Splunk Arcade Team

--------------------------------------------------------------------

Enjoy Editing Your Splunk Arcade Questions!