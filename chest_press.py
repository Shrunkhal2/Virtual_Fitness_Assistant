import cv2
import mediapipe as md
import tkinter as tk
import threading
import queue
import pyttsx3
import pygame
from playsound import playsound
import math

# Initialize pygame mixer for sound
pygame.mixer.init()

# Initialize the webcam
cap = cv2.VideoCapture(0)

cap.set(3, 1280)  # Set width
cap.set(4, 720)   # Set height

# Mediapipe Pose and drawing utilities
md_drawing = md.solutions.drawing_utils
md_pose = md.solutions.pose

# Counter for chest presses
count = 0

# Paths to audio files
buzzer = r"C:\Users\nupur bhatkhande\Desktop\buzzer.mp3"
welcome = r"C:\Users\nupur bhatkhande\Desktop\welcome.mp3"
motivational_music = r"C:\Users\nupur bhatkhande\Desktop\sq guide.mp3" 

# Text-to-speech engine
engine = pyttsx3.init()

# Queue to update count for voice coaching
update_queue = queue.Queue()

# Variables to track target count and music states
target_count = None
audio_played_flag = False
music_playing = False  
buzzer_played_flag = False

# State flags for tracking full motion cycle
in_bottom_position = False  # True when user is in the bottom position
in_top_position = False     # True when user is in the top position

def play_buzzer_once():
    global buzzer_played_flag
    if not buzzer_played_flag:
        playsound(buzzer)
        buzzer_played_flag = True

def voice_coaching_squat_count():
    global count
    while True:
        try:
            new_count = update_queue.get()
            if new_count is not None:
                count = new_count
                engine.say(count)
                engine.runAndWait()
        except queue.Empty:
            pass

def play_welcome_sound():
    playsound(welcome)

def play_motivational_music():
    global music_playing
    if not music_playing:
        pygame.mixer.music.load(motivational_music)
        pygame.mixer.music.play(0)  
        music_playing = True

def stop_motivational_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.stop()
        music_playing = False

def update_target_count():
    global target_count
    new_target = target_entry.get()
    if new_target == "":
        target_count.set("")  
    try:
        if new_target == "":
            stop_motivational_music()  
        else:
            new_target = int(new_target)
            if new_target >= 0:  
                target_count.set(new_target)  
                
                if not music_playing:
                    play_motivational_music()
            else:
                print("New target count should be a non-negative integer.")
    except ValueError:
        print("Please enter a valid number.")

def calculate_angle(point1, point2, point3):
    angle_radians = math.atan2(point3[1] - point2[1], point3[0] - point2[0]) - math.atan2(point1[1] - point2[1], point1[0] - point2[0])
    angle_degrees = math.degrees(angle_radians)
    angle_degrees = (angle_degrees + 360) % 360  
    return angle_degrees

def run_gui():
    global target_entry, target_count
    root = tk.Tk()
    root.title("Chest Press Counter")
    root.geometry("400x200")
    root.configure(bg="#f0f0f0")  

    frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)  
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Set Your Chest Press Target", font=("Helvetica", 14), bg="#ffffff")
    label.pack()

    target_entry = tk.Entry(frame, font=("Helvetica", 12))
    target_entry.insert(0, "10")  
    target_entry.pack()

    set_button = tk.Button(frame, text="Set Target", command=update_target_count, bg="#007acc", fg="#ffffff", font=("Helvetica", 12))
    set_button.pack()

    target_count = tk.StringVar(value="") 
    target_label = tk.Label(frame, textvariable=target_count, font=("Helvetica", 12), bg="#ffffff")
    target_label.pack()

    root.mainloop()

# Start GUI in a separate thread
gui_thread = threading.Thread(target=run_gui)
gui_thread.start()

# Start voice coaching thread
voice_coaching_thread = threading.Thread(target=voice_coaching_squat_count)
voice_coaching_thread.daemon = True
voice_coaching_thread.start()

# Play welcome sound
play_welcome_sound()

# Start pose detection and counting
with md_pose.Pose(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as pose:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Empty camera")
            break

        result = pose.process(image)

        if result.pose_landmarks:
            md_drawing.draw_landmarks(image, result.pose_landmarks, md_pose.POSE_CONNECTIONS)

            # Extract landmarks for posture analysis
            left_wrist = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_WRIST]
            left_elbow = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_ELBOW]
            left_shoulder = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_SHOULDER]

            # Calculate the angle at the elbow (wrist, elbow, shoulder)
            angle_wrist_elbow_shoulder = calculate_angle(
                (left_wrist.x, left_wrist.y),
                (left_elbow.x, left_elbow.y),
                (left_shoulder.x, left_shoulder.y)
            )

            # Define the angle ranges for bottom and top positions
            bottom_position_angle = 80   # Angle when the elbows are bent
            top_position_angle = 170     # Angle when the arms are fully extended

            # Visual feedback for posture correctness
            if 85 <= angle_wrist_elbow_shoulder <= 100:
                cv2.rectangle(image, (0, 0), (640, 60), (0, 255, 0), -1)  # Green background
                cv2.putText(image, "Correct Posture", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
            else:
                cv2.rectangle(image, (0, 0), (640, 60), (0, 0, 255), -1)  # Red background
                cv2.putText(image, "Incorrect Posture", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

            # Detect the bottom position (elbows bent)
            if angle_wrist_elbow_shoulder <= bottom_position_angle:
                in_bottom_position = True
                in_top_position = False  # Reset top position
                cv2.putText(image, "In Bottom Position", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Detect the top position (arms fully extended)
            elif angle_wrist_elbow_shoulder >= top_position_angle and in_bottom_position:
                in_top_position = True  # Reached top after starting at bottom
                cv2.putText(image, "In Top Position", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Only increment the count when a full cycle is completed: bottom -> top -> bottom
            if in_top_position and in_bottom_position:
                count += 1
                print(f"Rep Count: {count}")
                update_queue.put(count)  # Update the voice coaching system

                # Reset the cycle to await the next rep
                in_top_position = False
                in_bottom_position = False

        cv2.imshow("Chest Press Counter", image)

        # Check if target count is reached and play the buzzer
        try:
            new_target = target_count.get()
            if new_target != "" and count >= int(new_target):
                play_buzzer_once()
        except ValueError:
            pass

        # Exit condition
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()
