# AI-DCAS: AI-Driven Class Attendance System

[![PSMZA](https://img.shields.io/badge/Institution-PSMZA-blue.svg)](https://psmza.mypolycc.edu.my/) <!-- Optional: Gantikan dengan logo PSMZA jika ada -->
[![Status](https://img.shields.io/badge/Status-In%20Development-orange.svg)]() <!-- Tukar status jika perlu: Planning, Alpha, Beta, Released -->

An AI-Powered solution for automating class attendance tracking. This project is developed as a Final Year Project (FYP) for Politeknik Sultan Mizan Zainal Abidin (PSMZA), targeting completion in 2025.

## Table of Contents

*   [Introduction](#introduction)
*   [Problem Statement](#problem-statement)
*   [Objectives](#objectives)
*   [Features](#features)
*   [Technology Stack](#technology-stack)
*   [System Architecture](#system-architecture) <!-- Optional -->
*   [Installation](#installation)
*   [Usage](#usage)
*   [Project Status](#project-status)
*   [Team](#team)
*   [Acknowledgements](#acknowledgements)
*   [License](#license)

## Introduction

AI-DCAS (AI-Driven Class Attendance System) aims to modernize and streamline the process of recording student attendance in educational institutions. By leveraging Artificial Intelligence, specifically facial recognition technology <!-- Anda boleh tukar jika guna kaedah AI lain -->, this system automates attendance taking, reducing manual effort, minimizing errors, and providing accurate attendance data.

## Problem Statement

Traditional methods of taking attendance (e.g., manual roll calls, sign-in sheets) are often time-consuming, prone to inaccuracies (like buddy punching), and inefficient, especially for large classes. This manual process detracts valuable class time and administrative effort.

## Objectives

*   To develop an automated attendance system using AI.
*   To improve the accuracy and efficiency of attendance tracking.
*   To reduce the administrative burden on lecturers/instructors.
*   To provide a reliable and easily accessible record of student attendance.
*   To integrate technologies like Raspberry Pi and potential database solutions for a robust system. <!-- Sebut teknologi spesifik jika relevan -->

## Features

*   **Automated Attendance:** Captures attendance automatically using AI (e.g., facial recognition).
*   **Real-time Processing:** (Optional: if applicable) Processes attendance data quickly.
*   **Database Integration:** Stores attendance records securely.
*   **Reporting:** Generates attendance reports for analysis.
*   **User Interface:** (Optional: if applicable) Simple interface for administrators/lecturers.
*   _(Add more features as your project develops)_

## Technology Stack

*   **Programming Language:** Python <!-- Contoh, tukar jika lain -->
*   **AI/ML Libraries:** OpenCV, TensorFlow/Keras/PyTorch, face_recognition <!-- Contoh, pilih yang relevan -->
*   **Web Framework:** Flask / Django <!-- Jika ada web interface -->
*   **Database:** MySQL / PostgreSQL / SQLite <!-- Contoh -->
*   **Hardware:** Raspberry Pi, Camera Module <!-- Contoh -->
*   **Other:** Node-RED <!-- Jika digunakan -->

## System Architecture

<!-- Optional: Anda boleh masukkan gambarajah atau penerangan ringkas tentang arkitektur sistem di sini -->
_(Diagram/Description coming soon)_

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/AI-DCAS.git
cd AI-DCAS

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Setup database (add instructions here)
# ...

# Configure environment variables (add instructions here)
# ...
