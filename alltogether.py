import os
import json
import urllib.request
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Define constants
USER_DIR = os.path.expanduser("~")
GITHUB_REPO_URL = "https://api.github.com/repos/y2k04/dlscc/contents"
PROJECTS_DIR = os.path.join(USER_DIR, "AppData", "LocalLow", "SebastianLague", "Digital Logic Sim", "V1", "Projects")
CHIP_FILE_EXT = ".json"
DE = []

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chip Downloader</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
</head>
<body>
    <h1>Chip Downloader</h1>
    <form>
        <label for="project">Select a project:</label>
        <select id="project" name="project">
            {% for project in projects %}
                <option value="{{ project }}">{{ project }}</option>
            {% endfor %}
        </select>
        <br>
        <br>
        <label for="chip">Select a chip:</label>
        <select id="chip" name="chip">
            {% for chip in chips %}
                <option value="{{ chip }}">{{ chip }}</option>
            {% endfor %}
        </select>
        <br>
        <br>
        <button type="button" onclick="downloadChip()">Download Chip</button>
    </form>
    <div id="warnings"></div>
    <div id="status"></div>

    <script>
        function downloadChip() {
            var chip = document.getElementById("chip").value;
            var pro = document.getElementById("project").value;
            $.post("/download?chip="+chip+"&pro="+pro, function(data, status){
                document.getElementById("warnings").innerHTML = data.warnings;
                document.getElementById("status").innerHTML = data.hStatus;
            });
        }
    </script>
</body>
</html>

'''

def get_github_contents(url):
    """Retrieve the contents of a GitHub repository"""
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data

def available_projects():
    """Print the available project directories"""
    projects = []
    for dir_name in os.listdir(PROJECTS_DIR):
        if os.path.isdir(os.path.join(PROJECTS_DIR, dir_name)):
            projects.append(dir_name)
    return projects

def available_chips():
    """Print the available chip files"""
    chips = []
    chips_dir = get_github_contents(f"{GITHUB_REPO_URL}/69F3A590")
    for chip_file in chips_dir:
        if chip_file["name"].endswith(CHIP_FILE_EXT):
            chips.append(chip_file["name"])
    return chips

def download_chip(download_url, filename):
    """
    Downloads a file from the given URL and saves it with the given filename.

    Parameters:
        download_url (str): The URL to download the file from.
        filename (str): The name of the file to save the downloaded content to.

    Returns:
        bool: True if the file was successfully downloaded, False otherwise.
    """
    DE = []
    response = requests.get(download_url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        with open(filename, "r+") as f:
            content = f.read()
            f.seek(0)  # move the file pointer to the beginning of the file
            f.write(content.replace('69F3A590', ''))  # replace all instances of the string with an empty string    
            f.truncate()
        with open(filename, "r") as f:
            dependancies = json.load(f)
            for d in dependancies['Dependencies']:
                print(f'warning: dependancy{d} is required')
                DE.append("Warning: dependancy"+d+" is required")
            f.seek(0)
        return True
    else:
        print(f"Failed to download file from {download_url}")
        return False
def addChip(project_name, chip_name):
    # Check that project and chip exist
    if not os.path.isdir(os.path.join(PROJECTS_DIR, project_name)):
        print(f"Project '{project_name}' does not exist.")
        exit()
    if not chip_name.endswith(CHIP_FILE_EXT):
        chip_name += CHIP_FILE_EXT
    chips_dir = get_github_contents(f"{GITHUB_REPO_URL}/69F3A590")
    if not any(chip_file["name"] == chip_name for chip_file in chips_dir):
        print(f"Chip '{chip_name}' does not exist.")
        exit()

    # Download the specified chip file
    download_chip("https://raw.githubusercontent.com/y2k04/dlscc/repo/69F3A590/" + chip_name, os.path.join(PROJECTS_DIR, project_name, "Chips", chip_name.replace("69F3A590_","")))

    # Update project settings file
    settings_file = os.path.join(PROJECTS_DIR, project_name, "ProjectSettings.json")
    if not os.path.exists(settings_file):
        print(f"Project settings file not found: {settings_file}")
        exit()

    with open(settings_file, "r+") as f:
        settings = json.load(f)
        if "AllCreatedChips" not in settings:
            settings["AllCreatedChips"] = []
        settings["AllCreatedChips"].append(os.path.splitext(chip_name.replace("69F3A590_",""))[0])
        f.seek(0)
        json.dump(settings, f, indent=4)
        f.truncate()
    return

@app.route("/")
def home():
    """Display the home page"""
    projects = available_projects()
    chips = available_chips()
    return render_template_string(HTML, projects=projects, chips=chips)

@app.route("/download", methods=["POST"])
def download():
   chip = request.args.get("chip")
   project = request.args.get("pro")

   print(chip+project)

   addChip(project, chip)
   return jsonify(status=200, warnings=DE, hStatus="Chip downloaded succesfully")
    

while True:
    app.run()