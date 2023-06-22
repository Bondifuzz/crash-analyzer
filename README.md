# Crash analyzer

## Deployment

Download repository

```bash
git clone https://github.com/Bondifuzz/crash-analyzer.git
cd crash-analyzer
```

Build docker image

```bash
docker build -t crash-analyzer .
```

Run container (locally)

```bash
docker run --net=host --rm -it --name=crash-analyzer --env-file=.env crash-analyzer bash
```

## Local development

### Clone crash-analyzer repository

All code and scripts are placed to crash-analyzer repository. Let's clone it.

```bash
git clone https://github.com/Bondifuzz/crash-analyzer.git
cd crash-analyzer
```

### Start services crash-analyzer depends on

Then you should invoke `docker-compose` to start all services crash-analyzer depends on.

```bash
ln -s local/dotenv .env
ln -s local/docker-compose.yml docker-compose.yml
docker-compose -p crash-analyzer up -d
```

### Run crash-analyzer

Finally, you can run crash-analyzer service:

```bash
# Install dependencies
pip3 install -r requirements-dev.txt

# Run service
python3 -m crash_analyzer
```

### VSCode extensions

```bash
# Python
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance

# Spell checking
code --install-extension streetsidesoftware.code-spell-checker

# Config
code --install-extension redhat.vscode-yaml
code --install-extension tamasfe.even-better-toml

# Markdown
code --install-extension bierner.markdown-preview-github-styles
code --install-extension yzhang.markdown-all-in-one

# Developer
code --install-extension Gruntfuggly.todo-tree
code --install-extension donjayamanne.githistory
```

### Code documentation

TODO

### Running tests

```bash
# Install dependencies
pip3 install -r requirements-test.txt

# Run unit tests
pytest -vv crash-analyzer/tests/unit

# Run functional tests
pytest -vv crash-analyzer/tests/integration
```

### Spell checking

Download cspell and run to check spell in all sources

```bash
sudo apt install nodejs npm
sudo npm install -g cspell
cspell "**/*.{py,md,txt}"
```