# Estonian Text Simplification with OpenNMT

This project provides a Dockerized application for Estonian text simplification using an OpenNMT-based model. It includes a web interface and a RabbitMQ-based worker architecture for efficient processing.

---

## Features
- **Text Simplification**: Simplifies Estonian text using a pre-trained OpenNMT model.
- **Web Interface**: User-friendly interface for entering and simplifying text.
- **RabbitMQ Integration**: Decouples the worker process from the web server for scalable processing.
- **Dockerized**: Fully containerized for easy deployment.

---

## Prerequisites
1. **Docker**: Ensure Docker and Docker Compose are installed.
   - [Install Docker](https://docs.docker.com/get-docker/)
   - [Install Docker Compose](https://docs.docker.com/compose/install/)
2. **Model File**: Download the OpenNMT model from [Hugging Face](https://huggingface.co/).

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd webapp-opennmt
