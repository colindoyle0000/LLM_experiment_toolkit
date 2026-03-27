# Getting Started — LLM Experiment Toolkit

Follow these steps the first time you set up the toolkit on your computer.
After that, the only thing you'll ever need to do to get updates is run one
short command (described at the end).

---

## What you'll need before you start

- Your personal `.env` file (downloaded from Brightspace — it contains your
  API keys)


---

## Step 1: Install Git

Git is a free tool for downloading and updating software projects. You only
install it once.

**On a Mac:**

1. Open **Terminal** (press Cmd + Space, type "Terminal", press Enter).
2. Type this command and press Enter:
   ```
   git --version
   ```
3. If Git is already installed, you'll see a version number like
   `git version 2.39.3` — skip to Step 2.
4. If you see a dialog box asking you to install "command line developer
   tools," click **Install** and wait for it to finish. Then try again.
5. If you see an error with no dialog, go to
   [git-scm.com/download/mac](https://git-scm.com/download/mac) and
   download the installer.

**On Windows:**

1. Go to [git-scm.com/download/win](https://git-scm.com/download/win).
2. Download the installer and run it. Accept all the default options.
3. After installation, search for **Git Bash** in your Start menu and open
   it. Use Git Bash instead of Command Prompt for all commands in this guide.

---

## Step 2: Install Python

Python is the programming language the toolkit runs on.

1. In your terminal, type:
   ```
   python --version
   ```
2. If you see `Python 3.x.x` (any version starting with 3), you're good —
   skip to Step 3.
3. If you see `Python 2.x.x` or an error, go to
   [python.org/downloads](https://www.python.org/downloads/) and download
   the latest version. Run the installer.
   - **On Windows:** Check the box that says **"Add Python to PATH"** before
     clicking Install.
4. Close and reopen your terminal, then check again with `python --version`.

> **Note for Mac users:** If `python` doesn't work but `python3` does, use
> `python3` everywhere in this guide where you see `python`.

---

## Step 3: Download the project

This command copies the project folder from GitHub to your computer. You only
do this once.

In your terminal, navigate to a folder where you want to keep the project.
Your Documents folder is a good choice:

**On Mac:**
```
cd ~/Documents
```

**On Windows (Git Bash):**
```
cd ~/Documents
```

Then run this command to download the project:

```
git clone https://github.com/colindoyle0000/LLM_experiment_toolkit
```

After a moment you'll see some progress messages, and a new folder called
`LLM_experiment_toolkit` will appear in your Documents.

Now navigate into it:

```
cd LLM_experiment_toolkit
```

Leave the terminal window open — you'll use it in the next steps.

---

## Step 4: Add your .env file

Your `.env` file contains your personal API keys. It was posted privately for
you on Brightspace under assignments.

1. Download your `.env` file from Brightspace.
2. Move it into the `LLM_experiment_toolkit` folder you just downloaded.
   The file should sit alongside `README.md` and `run_experiment.py` —
   not inside any subfolder.

> **Important:** The file must be named exactly `.env` (with a dot at the
> start and no other extension). Some computers hide files that start with a
> dot — if you can't see it in Finder or File Explorer, that's normal. As
> long as you put it in the right folder, the toolkit will find it.

---

## Step 5: Install the toolkit's dependencies

The toolkit relies on a few additional software libraries. This command
downloads and installs them:

```
pip install -r requirements.txt
```

You'll see a list of packages being installed. This only needs to happen once.

> If you see an error about `pip`, try `pip3 install -r requirements.txt`
> instead.

> **Mac users — if you see "externally-managed-environment":** This is
> common on newer Macs. Run these two commands instead:
> ```
> python -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```
> Every time you open a new terminal window to run experiments, you'll need
> to run `source .venv/bin/activate` first (from the project folder).
> You'll know it's active when you see `(.venv)` at the start of your
> terminal prompt.

---

## Step 6: Verify everything works

Run this command to confirm your API keys are valid and everything is
installed correctly:

```
python verify_setup.py
```

You should see something like:

```
  Anthropic ... OK (claude-opus-4-6, 0.8s)
             Response: "Setup successful."

  OpenAI    ... OK (gpt-4o, 1.2s)
             Response: "Setup successful."

  Google    ... OK (gemini-2.5-flash, 0.6s)
             Response: "Setup successful."
```

- **OK** — that provider is working. You're ready to use it.
- **SKIPPED** — that API key is missing from your `.env` file. Check that
  the file is in the right folder and named correctly.
- **FAILED** — the key is present but not working. Double-check the `.env`
  file for typos, or contact your instructor.

Once at least one provider shows OK, you're ready to run experiments.

---

## You're set up. What's next?

Open `README.md` (it's in the project folder — you can open it in any text
editor or web browser). It covers:

- How to run an experiment
- How to create your own experiment
- How to read and analyze the results

---

## Getting updates

When the toolkit is updated on Github (usually to fix an error or add a new
feature), you can get the update with one command. In your terminal, navigate
to the project folder and run:

```
git pull
```

That's it. Your experiment files (in the `experiments/` folder) and your
`.env` file will not be touched — only the toolkit's core files will update.

> **If you get an error about "merge conflicts":** This usually means you
> accidentally edited a file outside the `experiments/` folder.
