
## 📘 Attendance Management - Academic Project

This is a **web-based Attendance Management System** designed for academic institutions. Built using **Flask** and **SQLite**, the system leverages **OpenCV** for face detection to automate attendance marking, providing a simple yet efficient platform for managing teacher and student interactions.

### ✨ Features

* 👨‍🏫 **Teacher and Student Login/Registration**
* 📸 **Face Detection-Based Attendance Marking**
* 📊 **Attendance Reports and Statistics**
* 📚 **Subject-wise & Overall Attendance Tracking**
* 🧑‍💻 **Modern, Easy-to-Use Web Interface**
* 🛡️ **Basic Role-Based Access for Teachers and Students**

### 🛠️ Technologies Used

* **Python** – Flask, SQLAlchemy
* **Computer Vision** – OpenCV, NumPy
* **Database** – SQLite (for local testing & development)
* **Frontend** – HTML, CSS, JavaScript (basic and responsive)

### 🚀 Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/attendance-management-academicproject.git
   cd attendance-management-academicproject
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**

   ```bash
   python app.py
   ```

4. **Access the App**

   * Open your browser and go to: `http://localhost:5000`

### 📌 Notes

* This project currently uses **SQLite** for simplicity. For production, consider switching to a remote database like **PostgreSQL**.
* Face recognition is simulated and doesn't perform real biometric matching. It can be extended with real-time recognition using face encodings or models like FaceNet or Dlib.

### 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change or improve.

---

