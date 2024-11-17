import cv2
import mediapipe as md
import tkinter as tk
import threading
import queue
import playsound
import math
import time
import pygame

# Initialize pygame
pygame.mixer.init()

# Initialize the video capture
cap = cv2.VideoCapture(0)

# Set the camera window size
cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height

md_drawing = md.solutions.drawing_utils
md_pose = md.solutions.pose

# Set the hold time threshold for Tadasana (in seconds)
hold_time_threshold = 100

# Define the paths to sound files
buzzer = r"C:\Users\nupur bhatkhande\Desktop\Relax.mp3"
welcome = r"C:\Users\nupur bhatkhande\Desktop\welcome.mp3"
# motivational_music = r"C:\Users\nupur bhatkhande\Desktop\yoga_guide.mp3"

# Create a queue to communicate between threads
update_queue = queue.Queue()

# Create global variables for target_count, target_entry, and audio_played_flag
target_count = None
music_playing = False  # Flag to track if motivational music is playing

# Create a flag to track whether the buzzer has been played
buzzer_played_flag = False

# Create a flag to indicate if the GUI has been initialized
gui_initialized = False

# Create a flag to indicate if Tadasana is currently being performed
tadasana_in_progress = False

# Initialize elapsed_time outside the loop
elapsed_time = 0

# Function to play the buzzer sound only once when the target is reached
def play_buzzer_once():
    global buzzer_played_flag
    if not buzzer_played_flag:
        playsound.playsound(buzzer)
        buzzer_played_flag = True

# Function to play the welcome sound
def play_welcome_sound():
    playsound.playsound(welcome)

# Function to play motivational music
def play_motivational_music():
    global music_playing
    if not music_playing:
        # pygame.mixer.music.load(motivational_music)
        pygame.mixer.music.play(0)  # Play the music in an infinite loop
        music_playing = True

# Function to stop motivational music
def stop_motivational_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.stop()
        music_playing = False

# Function to update the GUI with the target count
def update_gui():
    global target_count, target_label
    try:
        # Check if the target is updated
        new_target = target_count.get()
        if new_target != "":
            target_label.config(text=f"Target Hold Time: {new_target} seconds")
    except ValueError:
        pass
    root.after(1000, update_gui)  # Schedule the function to run again after 1000 milliseconds (1 second)

# Function to update the target count
def update_target_count():
    global target_count
    new_target = target_entry.get()
    if new_target == "":
        target_count.set("")  # Clear the target count if it's empty
    try:
        if new_target == "":
            stop_motivational_music()  # Stop the music if the target is cleared
        else:
            new_target = int(new_target)
            if new_target >= 0:  # Ensure the new target is a non-negative integer
                target_count.set(new_target)  # Set the new target count
                # If the music is not playing, start the music
                if not music_playing:
                    play_motivational_music()
            else:
                print("New target count should be a non-negative integer.")
    except ValueError:
        print("Please enter a valid number.")

# Function to calculate the angle between three points
def calculate_angle(point1, point2, point3):
    angle_radians = math.atan2(point3[1] - point2[1], point3[0] - point2[0]) - math.atan2(point1[1] - point2[1], point1[0] - point2[0])
    angle_degrees = math.degrees(angle_radians)
    angle_degrees = (angle_degrees + 360) % 360  # Ensure the angle is positive
    return angle_degrees

# Function to run Tadasana detection
def run_tadasana_detection():
    global tadasana_in_progress, tadasana_start_time, audio_played_flag, update_queue, elapsed_time

    with md_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as pose:

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Empty camera")
                break

            result = pose.process(image)

            # Initialize a flag to check full-body posture
            full_body_in_correct_position = False

            if result.pose_landmarks:
                md_drawing.draw_landmarks(
                    image, result.pose_landmarks, md_pose.POSE_CONNECTIONS)

                # Define landmarks for Tadasana detection
                left_shoulder = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = result.pose_landmarks.landmark[md_pose.PoseLandmark.RIGHT_SHOULDER]
                left_elbow = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_ELBOW]
                left_wrist = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_WRIST]
                right_elbow = result.pose_landmarks.landmark[md_pose.PoseLandmark.RIGHT_ELBOW]
                right_wrist = result.pose_landmarks.landmark[md_pose.PoseLandmark.RIGHT_WRIST]

                # Add this line to draw a vertical green line above the left shoulder
                cv2.line(image, (int(left_shoulder.x * image.shape[1]), 0), (int(left_shoulder.x * image.shape[1]), int(left_shoulder.y * image.shape[0])), (0, 255, 0), 2)
                # Add this line to draw a vertical green line above the right shoulder
                cv2.line(image, (int(right_shoulder.x * image.shape[1]), 0), (int(right_shoulder.x * image.shape[1]), int(right_shoulder.y * image.shape[0])), (0, 255, 0), 2)

                # Calculate the angles between body parts
                angle_left_shoulder_elbow_wrist = calculate_angle(
                    (left_shoulder.x, left_shoulder.y),
                    (left_elbow.x, left_elbow.y),
                    (left_wrist.x, left_wrist.y)
                )
                angle_right_shoulder_elbow_wrist = calculate_angle(
                    (right_shoulder.x, right_shoulder.y),
                    (right_elbow.x, right_elbow.y),
                    (right_wrist.x, right_wrist.y)
                )

                # Check for correct Tadasana posture
                if angle_left_shoulder_elbow_wrist > 175 and left_wrist.y < left_shoulder.y and \
                   angle_right_shoulder_elbow_wrist > 175 and right_wrist.y < right_shoulder.y:
                    cv2.rectangle(image, (10, 10), (100, 40), (0, 255, 0), -1)  # Green rectangle for correct posture
                    cv2.putText(image, "Correct Posture", (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    if not tadasana_in_progress:
                        tadasana_start_time = time.time()
                        tadasana_in_progress = True
                        audio_played_flag = False

                    elapsed_time = time.time() - tadasana_start_time

                    if elapsed_time >= hold_time_threshold and not audio_played_flag:
                        # Queue the hold time for voice coaching
                        update_queue.put(elapsed_time)
                        tadasana_in_progress = False
                        audio_played_flag = True

                else:
                    cv2.rectangle(image, (10, 10), (100, 40), (0, 0, 255), -1)  # Red rectangle for incorrect posture
                    cv2.putText(image, "Incorrect Posture", (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    # Add posture improvement instructions
                    cv2.putText(image, "Please maintain a correct Tadasana posture", (120, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    # If Tadasana is interrupted, reset the start time and audio flag
                    tadasana_start_time = None
                    tadasana_in_progress = False
                    audio_played_flag = False

            cv2.imshow("Tadasana Detector", image)

            try:
                # Check if the target is updated
                new_target = target_count.get()
                if new_target != "" and elapsed_time >= float(new_target):
                    play_buzzer_once()  # Play the buzzer sound only once when the target is reached
            except ValueError:
                pass

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

# Function to run the GUI
def run_gui():
    global target_entry, target_count, target_label, root, gui_initialized

    root = tk.Tk()
    root.title("Tadasana Detector")
    root.geometry("400x200")
    root.configure(bg="#f0f0f0")  # Set a background color

    frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)  # Create a frame with padding
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Set Your Tadasana Hold Time (sec)", font=("Helvetica", 14), bg="#ffffff")
    label.pack()

    target_entry = tk.Entry(frame, font=("Helvetica", 12))
    target_entry.insert(0, "10")  # Default value
    target_entry.pack()

    set_button = tk.Button(frame, text="Set Hold Time", command=update_target_count, bg="#007acc", fg="#ffffff", font=("Helvetica", 12))
    set_button.pack()

    target_count = tk.StringVar(value="")  # Initialize target count as empty initially
    target_label = tk.Label(frame, textvariable=target_count, font=("Helvetica", 12), bg="#ffffff")
    target_label.pack()

    update_gui()  # Start the function to update the GUI
    gui_initialized = True

    root.mainloop()

# Start the GUI thread
gui_thread = threading.Thread(target=run_gui)
gui_thread.start()

# Play the welcome sound
play_welcome_sound()

# Start the Tadasana detection thread
tadasana_thread = threading.Thread(target=run_tadasana_detection)
tadasana_thread.start()

# Wait for the GUI thread to finish
gui_thread.join()

# Stop motivational music when the program ends
stop_motivational_music()

# Release the camera and close windows
cap.release()
cv2.destroyAllWindows()
