import tkinter as tk
from tkinter import messagebox
import cv2
import dlib
import os
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime
import pyodbc

# Initialize Dlib's face detection and recognition models
detector = dlib.get_frontal_face_detector()
face_recognizer = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

last_recognized_user = None
last_detection = {}  


def get_employee_info(employee_number):
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=10.45.41.79,1433;'
            'DATABASE=QAS_Testing;'
            'UID=CREWISTRON;'
            'PWD=cre100;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM EMPLOYEES_DATA WHERE EMPLOYEE_NUM = ?", (employee_number,))
        result = cursor.fetchone()
        conn.close()
        if result:
            print(f"EMPLOYEE_NUM: {result.EMPLOYEE_NUM}, EMPLOYEE_NAME: {result.EMPLOYEE_NAME}, DEPARTMENT: {result.DEPARTMENT}")
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, result))
        return None
    except pyodbc.Error as e:
        print(f"An error occurred: {e}")
        return None

def get_latest_attendance_logs():
    logs = []
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=10.45.41.79,1433;'
            'DATABASE=Face_Attendance;'
            'UID=CREWISTRON;'
            'PWD=cre100;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()
        query = """
        SELECT TOP 14 employeeNumber, employeeName, department,
        CONVERT(VARCHAR, date, 23) as date, CONVERT(VARCHAR, timeIn, 8) as timeIn
        FROM employee_attendance_logs
        ORDER BY date DESC, timeIn DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        for row in results:
            logs.append({
                "employeeNumber": row.employeeNumber,
                "employeeName": row.employeeName,
                "department": row.department,
                "date": row.date,
                "timeIn": row.timeIn
            })
    except pyodbc.Error as e:
        print(f"An error occurred while fetching attendance logs: {e}")
    return logs

def insert_attendance_if_no_pending(employee_number, employee_name, department, date, time_in):
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=10.45.41.79,1433;'
            'DATABASE=Face_Attendance;'
            'UID=CREWISTRON;'
            'PWD=cre100;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()
        query_check = """
        SELECT COUNT(*) FROM employee_attendance_logs 
        WHERE employeeNumber = ? AND timeOut IS NULL
        """
        cursor.execute(query_check, (employee_number,))
        result = cursor.fetchone()
        if result[0] == 0:
            query_insert = """
            INSERT INTO employee_attendance_logs (employeeNumber, employeeName, department, date, timeIn, timeOut)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query_insert, (employee_number, employee_name, department, date, time_in, None))
            conn.commit()
        conn.close()
    except pyodbc.Error as e:
        print(f"An error occurred while logging attendance: {e}")


# Load profile images and their encodings
def load_profile_images(profile_folder):
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(profile_folder):
        filepath = os.path.join(profile_folder, filename)
        image = dlib.load_rgb_image(filepath)
        faces = detector(image, 1)

        if len(faces) > 0:
            shape = shape_predictor(image, faces[0])
            face_encoding = np.array(face_recognizer.compute_face_descriptor(image, shape))
            known_face_encodings.append(face_encoding)

            name = os.path.splitext(filename)[0]  # Extract name from file
            name = name.split('_')[0]
            known_face_names.append(name)
            print(f"✅ Face encoding loaded for {name}")
        else:
            print(f"❌ No face detected in: {filename}. Deleting image...")
            os.remove(filepath)  # Delete image with no detected face
    return known_face_encodings, known_face_names


# Load backup images for displaying when a face is recognized
def load_backup_images(backup_folder):
    backup_images = {}
    for filename in os.listdir(backup_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(backup_folder, filename)
            # Extract the base name without the index or extension
            base_name = os.path.splitext(filename)[0].split('_')[0]
            try:
                image = Image.open(img_path)
                backup_images[base_name] = image
                print(f"✅ Backup image loaded for {base_name}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return backup_images


# Update camera frames
def update_frame():
    # Process Left Camera
    ret_left, frame_left = cap.read()
    if ret_left:
        process_frame(frame_left, video_label)

    # Continue updating frames
    if start_button["state"] == tk.DISABLED:
        root.after(10, update_frame)


# Process each frame to detect and recognize faces
def process_frame(frame, video_label):
    #frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector(rgb_frame)

    for face in faces:
        shape = shape_predictor(rgb_frame, face)
        face_encoding = np.array(face_recognizer.compute_face_descriptor(rgb_frame, shape))
        name = "Unknown"
        confidence_percentage = 0  # Initialize confidence percentage

        if len(known_face_encodings) > 0:
            # Compare the detected face encoding with known ones
            distances = np.linalg.norm(known_face_encodings - face_encoding, axis=1)
            best_match_index = np.argmin(distances)
            confidence_percentage = (1 - distances[best_match_index]) * 100

            # Only consider it a match if confidence_percentage >= 70%
            if confidence_percentage >= 70:
                name = known_face_names[best_match_index]

        # Validate cropped area before saving
        top, bottom, left, right = face.top(), face.bottom(), face.left(), face.right()
        if top >= 0 and bottom <= rgb_frame.shape[0] and left >= 0 and right <= rgb_frame.shape[1]:
            cropped_image = Image.fromarray(rgb_frame[top:bottom, left:right])  # Crop face
            save_captured_face(cropped_image, name)  # Safe to call

        # Draw rectangles and write name + confidence
        x, y, w, h = (face.left(), face.top(), face.width(), face.height())

        # Show recognized name with confidence
        if name == "Unknown":
            display_text = f"{name} {round(confidence_percentage)}%"
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, display_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        else:
            display_text = f"{name} {round(confidence_percentage)}%"
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, display_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            # Display backup image for the recognized person
            display_backup_image(backup_image_label, name)

    # Display frame in Tkinter GUI
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    video_label.config(image=image)
    video_label.image = image
    
def display_attendance_table():
    canvas.delete("attendance_table")  # Clear existing rows and headers

    logs = get_latest_attendance_logs()
    if not logs:
        print("No attendance logs available.")
        return

    # Define column widths
    col_widths = [110, 110, 290, 110]  # Adjusted widths for [TIME IN, EMP#, NAME, DEPARTMENT]

    # Calculate total table width by summing the column widths
    total_table_width = sum(col_widths)

    # Table layout settings
    header_x = 10
    header_y = 10
    header_height = 30

    # Draw the table header
    canvas.create_rectangle(
        header_x, header_y, header_x + total_table_width, header_y + header_height,
        outline="black", fill="black", tags="attendance_table"
    )
    columns = ["TIME IN", "EMP#", "NAME", "DEPT"]

    # Draw each column header based on individual column widths
    col_start_x = header_x
    for col_index, (col_name, col_width) in enumerate(zip(columns, col_widths)):
        canvas.create_rectangle(
            col_start_x, header_y, col_start_x + col_width, header_y + header_height,
            outline="black", fill="black", tags="attendance_table"
        )
        canvas.create_text(
            col_start_x + 5, header_y + 5, anchor=tk.NW, text=col_name,
            fill="white", font=("Arial", 12, "bold"), tags="attendance_table"
        )
        col_start_x += col_width

    # Populate table rows
    row_y = header_y + header_height
    row_height = 30
    for log in logs:
        time_in_24hr = log['timeIn']
        try:
            time_in_obj = datetime.strptime(time_in_24hr, "%H:%M:%S")
            time_in = time_in_obj.strftime("%I:%M:%S %p")  # Convert to 12-hour format
        except ValueError:
            time_in = time_in_24hr  # Default to original if format conversion fails

        emp_number = log['employeeNumber']
        name = log['employeeName']
        department = log['department']
        row_data = [time_in, emp_number, name, department]

        # Draw table row
        canvas.create_rectangle(
            header_x, row_y, header_x + total_table_width, row_y + row_height,
            outline="black", fill="white", tags="attendance_table"
        )

        # Draw each cell based on individual column widths
        col_start_x = header_x
        for col_index, (data, col_width) in enumerate(zip(row_data, col_widths)):
            canvas.create_rectangle(
                col_start_x, row_y, col_start_x + col_width, row_y + row_height,
                outline="black", fill="white", tags="attendance_table"
            )
            canvas.create_text(
                col_start_x + 5, row_y + 5, anchor=tk.NW, text=data,
                fill="black", font=("Arial", 12), tags="attendance_table"
            )
            col_start_x += col_width  # Move to the next column

        row_y += row_height  # Move to the next row

def display_backup_image(backup_image_label, name):
    global last_recognized_user, last_detection  # Track the last recognized user and detection times

    # Ensure image exists for the name
    if name not in backup_images:
        print(f"No backup image available for {name}.")
        return
        
    if name == last_recognized_user:
        return

    current_time = datetime.now()

    if name in last_detection:
        time_since_last_detection = (current_time - last_detection[name]).total_seconds()
        if time_since_last_detection < 30:
            return

    last_detection[name] = current_time

    employee_info = get_employee_info(name) 
    if not employee_info:
        print(f"Employee data not found in database for {name}.")
        return 

    last_recognized_user = name 

    backup_image = backup_images[name]
    backup_image = backup_image.resize((300, 300), Image.LANCZOS) 
    backup_image_tk = ImageTk.PhotoImage(backup_image)

    backup_image_label.config(image=backup_image_tk)
    backup_image_label.image = backup_image_tk 

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time_db_format = datetime.now().strftime("%H:%M:%S") 

    emp_number = employee_info.get("EMPLOYEE_NUM", "")
    emp_name = employee_info.get("EMPLOYEE_NAME", "")
    department = employee_info.get("DEPARTMENT", "")

    insert_attendance_if_no_pending(
        employee_number=emp_number,
        employee_name=emp_name,
        department=department,
        date=current_date,
        time_in=current_time_db_format
    )

    update_recognized_info(
        name=emp_name,
        department=department,
        emp_number=emp_number,
        time=datetime.now().strftime("%I:%M:%S %p") 
    )

    display_attendance_table() 
     
# Function to update employee information labels
def update_recognized_info(name, department, emp_number, time):
    name_label_text = f"NAME: {name}"
    department_label_text = f"DEPARTMENT: {department}"
    emp_label_text = f"EMP#: {emp_number}"
    time_label_text = f"TIME: {time}"
    
    # Update each label with the new text
    name_label.config(text=name_label_text)
    department_label.config(text=department_label_text)
    emp_label.config(text=emp_label_text)
    time_label.config(text=time_label_text)



# Save the captured face images
def save_captured_face(cropped_image, name):
    now = datetime.now()

    # Create date and time strings
    year = now.strftime('%Y')
    month_name = now.strftime('%B')
    date_now = now.strftime('%d')
    time_now = now.strftime('%I-%M%p')

    # Create directory path record/year/month_name_date_now/
    directory = os.path.join('record', year, f"{month_name}_{date_now}")
    os.makedirs(directory, exist_ok=True)

    # Initialize base filename
    base_filename = f"{month_name}_{date_now}_{time_now}"
    index = 1
    filename = os.path.join(directory, f"{name}_{index}_{base_filename}.jpg")
    while os.path.exists(filename):
        index += 1
        filename = os.path.join(directory, f"{name}_{index}_{base_filename}.jpg")

    cropped_image.save(filename)


# Start Camera Feed
def start_camera():
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    update_frame()


# Stop Camera Feed
def stop_camera():
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)


# Exit Confirmation
def on_exit():
    cap.release()
    root.destroy()


# Main Execution
if __name__ == "__main__":
    # Initialize Cameras
    cap = cv2.VideoCapture(0)

    profile_folder = "profile"
    known_face_encodings, known_face_names = load_profile_images(profile_folder)
    backup_folder = "backup"
    backup_images = load_backup_images(backup_folder)

    # Tkinter GUI Setup
    root = tk.Tk()
    root.title("DTR Face Recognition")
    root.geometry("1300x800")

    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

    start_button = tk.Button(button_frame, text="Start", command=start_camera, width=8)
    start_button.pack(side=tk.LEFT, padx=(10, 0))

    stop_button = tk.Button(button_frame, text="Stop", command=stop_camera, width=8)
    stop_button.pack(side=tk.LEFT)
    stop_button.config(state=tk.DISABLED)

    camera_frame = tk.Frame(root)
    camera_frame.pack(side=tk.TOP, fill=tk.X)

    video_label = tk.Label(camera_frame, text="TIME IN")
    video_label.pack(side=tk.LEFT, padx=(10, 0))
    
    table_frame = tk.Label(camera_frame, text="TABLE")
    table_frame.pack(side=tk.LEFT)

    canvas = tk.Canvas(table_frame, width=640, height=480, bg="white")
    canvas.pack()
    
    picture_frame = tk.Frame(root)
    picture_frame.pack(side=tk.TOP, fill=tk.X)
    
    info_frame = tk.Frame(picture_frame)
    info_frame.pack(side=tk.LEFT, padx=(10, 0)) 

    backup_image_label = tk.Label(info_frame, text="No Image")
    backup_image_label.pack(side=tk.LEFT)

    info_text_frame = tk.Frame(info_frame)
    info_text_frame.pack(side=tk.TOP, padx=(10, 0), pady=(10, 0))

    name_label = tk.Label(info_text_frame, text="NAME: ", font=("Arial", 35, "bold"), fg="black")
    name_label.pack(anchor="nw") 

    department_label = tk.Label(info_text_frame, text="DEPARTMENT: ", font=("Arial", 35, "bold"), fg="black")
    department_label.pack(anchor="nw") 
    
    emp_label = tk.Label(info_text_frame, text="EMP#: ", font=("Arial", 35, "bold"), fg="black")
    emp_label.pack(anchor="nw")  

    time_label = tk.Label(info_text_frame, text="TIME: ", font=("Arial", 60, "bold"), fg="black")
    time_label.pack(anchor="nw")  

    
    root.mainloop()

