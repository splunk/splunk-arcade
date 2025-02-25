const express = require("express");
const fs = require("fs");
const path = require("path");
const minimist = require("minimist");
const app = express();
const PORT = 3000;

// Constants
const DEFAULT_FILE_PATH = path.resolve(__dirname, "../../player-content/questions-test.json");
const args = minimist(process.argv.slice(2));
const FILE_PATH = args.f ? path.resolve(args.f) : DEFAULT_FILE_PATH;
const PAGE_TITLE = "Splunk Arcade Questions Editor"; // Title Constant

app.use(express.json());
app.use(express.static("public"));

// Load JSON data
app.get("/questions", (req, res) => {
    fs.readFile(FILE_PATH, "utf8", (err, data) => {
        if (err) {
            return res.status(500).json({ error: "Error reading file: " + FILE_PATH });
        }
        res.json(JSON.parse(data));
    });
});

// Save JSON data
app.post("/questions", (req, res) => {
    fs.writeFile(FILE_PATH, JSON.stringify(req.body, null, 2), "utf8", (err) => {
        if (err) {
            return res.status(500).json({ error: "Error writing file: " + FILE_PATH });
        }
        res.json({ message: "File saved successfully" });
    });
});

app.listen(PORT, () => {
    console.log("Server running on http://localhost:" + PORT);
    console.log("Using JSON file: " + FILE_PATH);
});

// Ensure the public folder exists
const publicPath = path.join(__dirname, "public");
if (!fs.existsSync(publicPath)) {
    fs.mkdirSync(publicPath);
}

// Write the frontend file
const indexHtmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${PAGE_TITLE}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        input[type="text"] { width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; }
        textarea { width: 100%; height: 100px; padding: 8px; margin: 5px 0; box-sizing: border-box; }
        button { padding: 10px; margin-top: 10px; font-size: 16px; cursor: pointer; }
        h2, h3 { margin-top: 20px; }
        .container { max-width: 1200px; margin: auto; }
    </style>
    <script>
        let currentCategoryIndex = 0;
        let categories = [];
        let data = {};

        async function loadQuestions() {
            const response = await fetch("/questions");
            data = await response.json();
            categories = Object.keys(data);
            if (categories.length === 0) {
                document.getElementById("formContainer").innerHTML = "<p>No questions found.</p>";
                return;
            }
            currentCategoryIndex = 0;
            renderCategory();
        }

        function renderCategory() {
            const formContainer = document.getElementById("formContainer");
            formContainer.innerHTML = "";

            if (categories.length === 0) return;

            const category = categories[currentCategoryIndex];
            const categoryDiv = document.createElement("div");
            categoryDiv.innerHTML = "<h2>" + category + "</h2>";

            data[category].forEach((item, index) => {
                const itemDiv = document.createElement("div");
                let choicesHTML = "";

                item.choices.forEach((choice, cIndex) => {
                    choicesHTML += "<label>Choice " + (cIndex + 1) + ": <input type='text' name='choice_" + category + "_" + index + "_" + cIndex + "' value='" + choice.prompt + "' /></label>";
                    choicesHTML += "<label>Correct: <input type='checkbox' name='correct_" + category + "_" + index + "_" + cIndex + "' " + (choice.is_correct ? "checked" : "") + " /></label><br>";
                });

                itemDiv.innerHTML = "<h3>Question " + (index + 1) + "</h3>" +
                    "<label>Question: <input type='text' name='question_" + category + "_" + index + "' value='" + item.question + "' /></label><br>" +
                    (item.link ? "<label>Link: <input type='text' name='link_" + category + "_" + index + "' value='" + item.link + "' /></label><br>" : "") +
                    (item.link_text ? "<label>Link Text: <input type='text' name='link_text_" + category + "_" + index + "' value='" + item.link_text + "' /></label><br>" : "") +
                    "<h4>Choices:</h4>" + choicesHTML +
                    "<button onclick='deleteQuestion(" + index + ")'>❌ Delete Question</button><hr>";

                categoryDiv.appendChild(itemDiv);
            });

            formContainer.appendChild(categoryDiv);
        }

        function deleteQuestion(index) {
            const category = categories[currentCategoryIndex];

            if (data[category].length > 1) {
                data[category].splice(index, 1);
            } else {
                alert("⚠️ Cannot delete the last question in this category!");
                return;
            }

            renderCategory();
        }

        async function saveQuestions() {
            let isValid = true;
            let errorMessage = "";

            const formData = new FormData(document.getElementById("jsonForm"));
            const updatedData = {};

            formData.forEach((value, key) => {
                const parts = key.split("_");
                if (parts[0] === "question") {
                    const category = parts[1], index = parseInt(parts[2]);
                    if (!updatedData[category]) updatedData[category] = [];
                    if (!updatedData[category][index]) updatedData[category][index] = { choices: [] };
                    updatedData[category][index].question = value;
                } else if (parts[0] === "choice") {
                    const category = parts[1], index = parseInt(parts[2]), choiceIndex = parseInt(parts[3]);
                    updatedData[category][index].choices[choiceIndex] = { prompt: value };
                }
            });

            document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
                const parts = checkbox.name.split("_");
                if (parts[0] === "correct") {
                    const category = parts[1], index = parseInt(parts[2]), choiceIndex = parseInt(parts[3]);
                    updatedData[category][index].choices[choiceIndex].is_correct = checkbox.checked;
                }
            });

            for (let category in updatedData) {
                updatedData[category].forEach((question, index) => {
                    if (question.choices.filter(choice => choice.is_correct).length !== 1) {
                        isValid = false;
                        errorMessage += "❌ Error in " + category + " Question " + (index + 1) + ": Must have exactly one correct answer.\\n";
                    }
                });
            }

            if (!isValid) {
                alert(errorMessage);
                return;
            }

            data = updatedData;
            await fetch("/questions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });

            alert("✅ JSON saved successfully!");
        }

        window.onload = loadQuestions;
    </script>
</head>
<body>
    <div class="container">
        <h1>${PAGE_TITLE}</h1>
        <form id="jsonForm">
            <div id="formContainer"></div>
            <button type="button" onclick="saveQuestions()">Save</button>
        </form>
    </div>
</body>
</html>`;

fs.writeFileSync(path.join(publicPath, "index.html"), indexHtmlContent, "utf8");