<div align="center">
<h1 align="center">
<img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" width="100" />
<br>ft_transcandance</h1>
<h3>◦ PokePong game !</h3>
</div>

## 📍 Overview
This repository is about the final project of the 42 Commun core. It's a web pong game realised with threejs, django, bootstarp toolkit and native js. All of the scores are also stored in a local blockchain.
---

## 🚀 Getting Started

***Dependencies***

Please ensure you have the following dependencies installed on your system:

`make, python3, docker`

## 🔧 Installation

1. Clone the git repository:
```sh
git clone https://github.com/ethaaalpha/ft_transcendance
```

2. Change to the project directory:
```sh
cd ft_transcendance
```

3. Run the project (read the .env part) :
### If a .env file is not present in the project directory, make will run env.py to set it up.
```sh
make
```

### 🗺️ Additional Resources
GitMind Map
For a visual representation of the project structure and dependencies, please refer to the [GitMind Map](https://gitmind.com/app/docs/mifuc2mn).

API Documentation
Detailed information about the API endpoints, request/response formats, and more can be found in the [API Documentation](https://lace-colt-015.notion.site/API-Documentation-a2487bcd1b25426f878f6313bcd9f88d?pvs=4).

Database Map
The structure of the project's database can be explored through the [Database Map](https://gh.atlasgo.cloud/explore/158d8759).

### 📄 .env File
The project requires a .env file to function correctly. This file should contain the following variables:

```Makefile
# Default Config Docker
DOMAIN = ''

# PostgreSQL
DB_PASSWORD = ''
DB_USER = ''
DB_NAME = ''

# Django

## API - 42
API_CALLBACK = ""
API_URL = ""
API_UUID = ""
API_SECRET = ""
API_TOKEN = ""
API_INFO = ""

## Mailing
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

## Django Key
SECRET_KEY=''

# Ethereum Network
NODE1_ACCOUNT_PASSWORD=''
NODE2_ACCOUNT_PASSWORD=''
NETWORK_ID=
```

Please replace the empty strings ('') with your actual configuration values.  
The **email** service is using *smtp.gmail.com* server.

---

[**Return**](#Top)

---